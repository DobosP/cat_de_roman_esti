//! Bounded anonymous game sessions, with independent transactional locks.

use std::collections::{BTreeMap, HashMap};
use std::fmt;
use std::sync::{Arc, Mutex, MutexGuard};
use std::time::{Duration, Instant};
mod config;

pub const DEFAULT_TTL: Duration = Duration::from_secs(7200);
pub const DEFAULT_MAX_SESSIONS: usize = 1000;

pub type Clock = dyn Fn() -> Duration + Send + Sync;

#[derive(Debug, PartialEq, Eq)]
pub enum StoreError {
    Capacity,
    Entropy,
    Configuration,
}

impl fmt::Display for StoreError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(match self {
            Self::Capacity => "all session slots are currently busy",
            Self::Entropy => "session identity generation failed",
            Self::Configuration => "invalid session store configuration",
        })
    }
}

impl std::error::Error for StoreError {}

fn lock<T>(mutex: &Mutex<T>) -> MutexGuard<'_, T> {
    // A callback panic must not leak a pin or permanently poison the store.
    mutex
        .lock()
        .unwrap_or_else(|poisoned| poisoned.into_inner())
}

struct Record<T> {
    value: Arc<Mutex<T>>,
    last_access: Duration,
    order: u64,
    borrowers: usize,
}

struct Metadata<T> {
    records: HashMap<String, Record<T>>,
    lru: BTreeMap<u64, String>,
    next_order: u64,
}

impl<T> Metadata<T> {
    fn remove(&mut self, id: &str) {
        if let Some(record) = self.records.remove(id) {
            self.lru.remove(&record.order);
        }
    }

    fn allocate_order(&mut self) -> u64 {
        if self.next_order == u64::MAX {
            // Renumbering retains the order and the fixed size after a theoretical
            // sequence-counter rollover, rather than growing a history of locks.
            let ids: Vec<String> = self.lru.values().cloned().collect();
            self.lru.clear();
            for (order, id) in ids.into_iter().enumerate() {
                self.records.get_mut(&id).unwrap().order = order as u64;
                self.lru.insert(order as u64, id);
            }
            self.next_order = self.records.len() as u64;
        }
        let order = self.next_order;
        self.next_order += 1;
        order
    }

    fn touch(&mut self, id: &str, now: Duration) {
        let old_order = self.records[id].order;
        let owned_id = self.lru.remove(&old_order).unwrap();
        let order = self.allocate_order();
        let record = self.records.get_mut(id).unwrap();
        record.order = order;
        record.last_access = now;
        self.lru.insert(order, owned_id);
    }

    fn purge(&mut self, now: Duration, ttl: Option<f64>) -> usize {
        let Some(ttl) = ttl else { return 0 };
        let mut expired = Vec::new();
        for id in self.lru.values() {
            let record = &self.records[id];
            if now.saturating_sub(record.last_access).as_secs_f64() <= ttl {
                break;
            }
            if record.borrowers == 0 {
                expired.push(id.clone());
            }
        }
        let removed = expired.len();
        for id in expired {
            self.remove(&id);
        }
        removed
    }
}

/// Locks and LRU metadata live only inside the capped store. Its monotonic clock
/// is injectable for deterministic tests; expiry and eviction are lazy.
pub struct Store<T> {
    metadata: Mutex<Metadata<T>>,
    ttl: Option<f64>,
    max_sessions: Option<usize>,
    clock: Arc<Clock>,
}

struct Pin<'a, T> {
    store: &'a Store<T>,
    id: &'a str,
}

impl<T> Drop for Pin<'_, T> {
    fn drop(&mut self) {
        let mut metadata = lock(&self.store.metadata);
        if let Some(record) = metadata.records.get_mut(self.id) {
            record.borrowers -= 1;
        }
    }
}

impl<T> Default for Store<T> {
    fn default() -> Self {
        Self::new()
    }
}

impl<T> Store<T> {
    pub fn new() -> Self {
        let config = config::from_env().unwrap_or_else(|error| panic!("{error}"));
        let start = Instant::now();
        let mut store = Self::with_options(
            Some(DEFAULT_TTL),
            Some(config.max_sessions),
            Arc::new(move || start.elapsed()),
        )
        .unwrap();
        store.ttl = Some(config.ttl_seconds);
        store
    }

    /// None disables the corresponding bound. The clock must never move back.
    /// Production callers use new(), which always retains both limits.
    pub fn with_options(
        ttl: Option<Duration>,
        max_sessions: Option<usize>,
        clock: Arc<Clock>,
    ) -> Result<Self, StoreError> {
        if max_sessions == Some(0) {
            return Err(StoreError::Configuration);
        }
        Ok(Self {
            metadata: Mutex::new(Metadata {
                records: HashMap::new(),
                lru: BTreeMap::new(),
                next_order: 0,
            }),
            ttl: ttl.map(|value| value.as_secs_f64()),
            max_sessions,
            clock,
        })
    }

    pub fn create(&self, value: T) -> Result<String, StoreError> {
        let (id, mut metadata) = loop {
            let id = uuid()?;
            let metadata = lock(&self.metadata);
            if !metadata.records.contains_key(&id) {
                break (id, metadata);
            }
        };
        let now = (self.clock)();
        metadata.purge(now, self.ttl);
        if self
            .max_sessions
            .is_some_and(|max| metadata.records.len() >= max)
        {
            let idle = metadata
                .lru
                .values()
                .find(|id| metadata.records[*id].borrowers == 0)
                .cloned();
            match idle {
                Some(id) => metadata.remove(&id),
                None => return Err(StoreError::Capacity),
            }
        }
        let order = metadata.allocate_order();
        metadata.lru.insert(order, id.clone());
        metadata.records.insert(
            id.clone(),
            Record {
                value: Arc::new(Mutex::new(value)),
                last_access: now,
                order,
                borrowers: 0,
            },
        );
        Ok(id)
    }

    /// Pins both running and waiting transactions before releasing the metadata
    /// lock. The callback must not recursively transact on the same id. Returned
    /// responses must own their data, rather than retaining a mutable reference.
    pub fn transaction<R>(&self, id: &str, callback: impl FnOnce(&mut T) -> R) -> Option<R> {
        let value = {
            let mut metadata = lock(&self.metadata);
            metadata.purge((self.clock)(), self.ttl);
            let record = metadata.records.get_mut(id)?;
            record.borrowers += 1;
            Arc::clone(&record.value)
        };
        // Declaration order ensures the entry guard drops before its pin, even
        // during callback unwinding. No global lock is held while waiting.
        let pin = Pin { store: self, id };
        let mut guard = lock(&value);
        lock(&self.metadata).touch(id, (self.clock)());
        let result = callback(&mut guard);
        drop(guard);
        drop(pin);
        Some(result)
    }

    pub fn delete(&self, id: &str) -> bool {
        let mut metadata = lock(&self.metadata);
        if metadata
            .records
            .get(id)
            .is_none_or(|record| record.borrowers != 0)
        {
            return false;
        }
        metadata.remove(id);
        true
    }

    pub fn purge_expired(&self) -> usize {
        lock(&self.metadata).purge((self.clock)(), self.ttl)
    }

    pub fn len(&self) -> usize {
        let mut metadata = lock(&self.metadata);
        metadata.purge((self.clock)(), self.ttl);
        metadata.records.len()
    }

    pub fn is_empty(&self) -> bool {
        self.len() == 0
    }
}

fn uuid() -> Result<String, StoreError> {
    let mut bytes = [0u8; 16];
    getrandom::fill(&mut bytes).map_err(|_| StoreError::Entropy)?;
    bytes[6] = bytes[6] & 0x0f | 0x40;
    bytes[8] = bytes[8] & 0x3f | 0x80;
    let hex: String = bytes.iter().map(|byte| format!("{byte:02x}")).collect();
    Ok(format!(
        "{}-{}-{}-{}-{}",
        &hex[..8],
        &hex[8..12],
        &hex[12..16],
        &hex[16..20],
        &hex[20..]
    ))
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::panic::{AssertUnwindSafe, catch_unwind};
    use std::sync::atomic::{AtomicU64, Ordering};
    use std::sync::mpsc::{channel, sync_channel};
    use std::thread;

    fn test_store<T>(ttl: Option<Duration>, cap: Option<usize>) -> (Arc<Store<T>>, Arc<AtomicU64>) {
        let now = Arc::new(AtomicU64::new(0));
        let clock_now = Arc::clone(&now);
        let store = Store::with_options(
            ttl,
            cap,
            Arc::new(move || Duration::from_nanos(clock_now.load(Ordering::SeqCst))),
        )
        .unwrap();
        (Arc::new(store), now)
    }

    fn advance(now: &AtomicU64, duration: Duration) {
        now.fetch_add(duration.as_nanos() as u64, Ordering::SeqCst);
    }

    #[test]
    fn ttl_boundary_slides_on_access_and_lru_eviction_is_bounded() {
        let (store, now) = test_store(Some(Duration::from_secs(10)), Some(2));
        let first = store.create(1).unwrap();
        let second = store.create(2).unwrap();
        advance(&now, Duration::from_secs(10));
        assert_eq!(store.transaction(&first, |value| *value), Some(1));
        let third = store.create(3).unwrap();
        assert_eq!(store.transaction(&second, |value| *value), None);
        assert_eq!(store.transaction(&first, |value| *value), Some(1));
        assert_eq!(store.transaction(&third, |value| *value), Some(3));
        advance(&now, Duration::from_secs(10) + Duration::from_nanos(1));
        assert_eq!(store.len(), 0);
        assert_eq!(first.len(), 36);
        assert_eq!(&first[14..15], "4");
        assert_ne!(first, second);
    }

    #[test]
    fn pinned_sessions_cannot_expire_delete_or_exceed_capacity() {
        let (store, now) = test_store(Some(Duration::from_secs(1)), Some(1));
        let id = store.create(1).unwrap();
        let (entered_tx, entered_rx) = sync_channel(0);
        let (release_tx, release_rx) = sync_channel(0);
        let worker_store = Arc::clone(&store);
        let worker_id = id.clone();
        let worker = thread::spawn(move || {
            worker_store.transaction(&worker_id, |_| {
                entered_tx.send(()).unwrap();
                release_rx.recv().unwrap();
            })
        });
        entered_rx.recv().unwrap();
        advance(&now, Duration::from_secs(2));
        assert_eq!(store.purge_expired(), 0);
        assert_eq!(store.len(), 1);
        assert!(!store.delete(&id));
        assert_eq!(store.create(2), Err(StoreError::Capacity));
        release_tx.send(()).unwrap();
        worker.join().unwrap();
        assert_eq!(store.purge_expired(), 1);
    }

    #[test]
    fn pinned_old_entry_does_not_block_expiry_of_younger_idle_entry() {
        let (store, now) = test_store(Some(Duration::from_secs(1)), Some(2));
        let id = store.create(1).unwrap();
        let (entered_tx, entered_rx) = sync_channel(0);
        let (release_tx, release_rx) = sync_channel(0);
        let worker_store = Arc::clone(&store);
        let worker = thread::spawn(move || {
            worker_store.transaction(&id, |_| {
                entered_tx.send(()).unwrap();
                release_rx.recv().unwrap();
            })
        });
        entered_rx.recv().unwrap();
        store.create(2).unwrap();
        advance(&now, Duration::from_secs(2));
        assert_eq!(store.purge_expired(), 1);
        release_tx.send(()).unwrap();
        worker.join().unwrap();
    }

    #[test]
    fn queued_transactions_pin_and_touch_only_on_lock_acquisition() {
        let (store, now) = test_store(Some(Duration::from_secs(1)), Some(1));
        let id = store.create(1).unwrap();
        let (entered_tx, entered_rx) = sync_channel(0);
        let (release_tx, release_rx) = sync_channel(0);
        let worker_store = Arc::clone(&store);
        let worker_id = id.clone();
        let worker = thread::spawn(move || {
            worker_store.transaction(&worker_id, |_| {
                entered_tx.send(()).unwrap();
                release_rx.recv().unwrap();
            })
        });
        entered_rx.recv().unwrap();
        let waiter_store = Arc::clone(&store);
        let waiter_id = id.clone();
        let waiter = thread::spawn(move || waiter_store.transaction(&waiter_id, |_| ()));
        let deadline = Instant::now() + Duration::from_secs(3);
        loop {
            if lock(&store.metadata).records[&id].borrowers == 2 {
                break;
            }
            assert!(Instant::now() < deadline, "waiter never pinned");
            thread::yield_now();
        }
        advance(&now, Duration::from_secs(2));
        assert_eq!(store.create(2), Err(StoreError::Capacity));
        release_tx.send(()).unwrap();
        worker.join().unwrap();
        waiter.join().unwrap();
        assert!(store.transaction(&id, |_| ()).is_some());
    }

    #[test]
    fn independent_sessions_run_without_global_lock_and_updates_are_atomic() {
        let (store, _) = test_store(None, Some(2));
        let id = store.create(0usize).unwrap();
        let other = store.create(0).unwrap();
        let workers: Vec<_> = (0..64)
            .map(|_| {
                let store = Arc::clone(&store);
                let id = id.clone();
                thread::spawn(move || store.transaction(&id, |value| *value += 1))
            })
            .collect();
        for worker in workers {
            worker.join().unwrap();
        }
        assert_eq!(store.transaction(&id, |value| *value), Some(64));
        let (entered_tx, entered_rx) = sync_channel(0);
        let (release_tx, release_rx) = sync_channel(0);
        let worker_store = Arc::clone(&store);
        let worker = thread::spawn(move || {
            worker_store.transaction(&id, |_| {
                entered_tx.send(()).unwrap();
                release_rx.recv().unwrap();
            })
        });
        entered_rx.recv().unwrap();
        let (done_tx, done_rx) = channel();
        let other_store = Arc::clone(&store);
        let other_worker = thread::spawn(move || {
            other_store.transaction(&other, |value| *value = 99);
            done_tx.send(()).unwrap();
        });
        done_rx.recv_timeout(Duration::from_secs(3)).unwrap();
        release_tx.send(()).unwrap();
        worker.join().unwrap();
        other_worker.join().unwrap();
    }

    #[test]
    fn callback_panics_and_missing_ids_cannot_leak_locks_or_pins() {
        let (store, _) = test_store(None, Some(1));
        let id = store.create(1).unwrap();
        let result = catch_unwind(AssertUnwindSafe(|| {
            store.transaction(&id, |_| panic!("callback"))
        }));
        assert!(result.is_err());
        assert_eq!(store.transaction(&id, |value| *value), Some(1));
        assert!(store.delete(&id));
        for id in 0..1000 {
            assert!(store.transaction(&id.to_string(), |_| ()).is_none());
        }
        assert!(store.is_empty());
        assert!(Store::<u8>::with_options(None, Some(0), Arc::new(|| Duration::ZERO)).is_err());
        assert_eq!(DEFAULT_TTL, Duration::from_secs(7200));
        assert_eq!(DEFAULT_MAX_SESSIONS, 1000);
    }
}
