//! Integer-seeded CPython `random.Random` operations for puzzle compatibility.
//! MT19937 is used for deterministic games, never credentials or session IDs.

use num_bigint::{BigInt, BigUint};

const STATE_SIZE: usize = 624;

pub struct Random {
    state: [u32; STATE_SIZE],
    index: usize,
}

impl Random {
    /// Python seeds integers by their absolute value, expanded into low words
    /// first. The caller supplies OS entropy through `from_words` for an
    /// unseeded game; independent entropy cannot have deterministic parity.
    pub fn new(seed: &BigInt) -> Self {
        let (_, words) = seed.to_u32_digits();
        Self::from_words(&words)
    }

    pub fn from_u64(seed: u64) -> Self {
        let low = seed as u32;
        let high = (seed >> 32) as u32;
        if high == 0 {
            Self::from_words(&[low])
        } else {
            Self::from_words(&[low, high])
        }
    }

    pub fn from_decimal(seed: &str) -> Option<Self> {
        BigInt::parse_bytes(seed.as_bytes(), 10).map(|value| Self::new(&value))
    }

    pub fn from_words(words: &[u32]) -> Self {
        let zero = [0];
        let words = if words.is_empty() { &zero[..] } else { words };
        let mut rng = Self {
            state: [0; STATE_SIZE],
            index: STATE_SIZE,
        };
        rng.state[0] = 19_650_218;
        for i in 1..STATE_SIZE {
            let previous = rng.state[i - 1];
            rng.state[i] = 1_812_433_253u32
                .wrapping_mul(previous ^ (previous >> 30))
                .wrapping_add(i as u32);
        }
        let (mut i, mut j) = (1, 0);
        for _ in 0..STATE_SIZE.max(words.len()) {
            let previous = rng.state[i - 1];
            rng.state[i] = (rng.state[i] ^ (previous ^ (previous >> 30)).wrapping_mul(1_664_525))
                .wrapping_add(words[j])
                .wrapping_add(j as u32);
            i += 1;
            j += 1;
            if i >= STATE_SIZE {
                rng.state[0] = rng.state[STATE_SIZE - 1];
                i = 1;
            }
            if j >= words.len() {
                j = 0;
            }
        }
        for _ in 0..STATE_SIZE - 1 {
            let previous = rng.state[i - 1];
            rng.state[i] = (rng.state[i]
                ^ (previous ^ (previous >> 30)).wrapping_mul(1_566_083_941))
            .wrapping_sub(i as u32);
            i += 1;
            if i >= STATE_SIZE {
                rng.state[0] = rng.state[STATE_SIZE - 1];
                i = 1;
            }
        }
        rng.state[0] = 0x8000_0000;
        rng
    }

    /// The next full-width output is Python `getrandbits(32)`.
    pub fn next_u32(&mut self) -> u32 {
        if self.index >= STATE_SIZE {
            for i in 0..STATE_SIZE {
                let y = (self.state[i] & 0x8000_0000)
                    | (self.state[(i + 1) % STATE_SIZE] & 0x7fff_ffff);
                self.state[i] = self.state[(i + 397) % STATE_SIZE] ^ (y >> 1);
                if y & 1 != 0 {
                    self.state[i] ^= 0x9908_b0df;
                }
            }
            self.index = 0;
        }
        let mut value = self.state[self.index];
        self.index += 1;
        value ^= value >> 11;
        value ^= (value << 7) & 0x9d2c_5680;
        value ^= (value << 15) & 0xefc6_0000;
        value ^= value >> 18;
        value
    }

    /// Python uses the high bits of partial words and places full words at the
    /// low end first. Zero bits returns zero without consuming random state.
    pub fn getrandbits(&mut self, bits: usize) -> BigUint {
        let mut words = Vec::with_capacity(bits.div_ceil(32));
        for offset in (0..bits).step_by(32) {
            let mut value = self.next_u32();
            let remaining = bits - offset;
            if remaining < 32 {
                value >>= 32 - remaining;
            }
            words.push(value);
        }
        BigUint::new(words)
    }

    /// Rejection sampling intentionally takes an extra bit for powers of two,
    /// matching Python's `_randbelow_with_getrandbits`.
    pub fn randbelow(&mut self, upper: usize) -> usize {
        assert!(upper > 0, "pyrandom: empty range");
        let bits = usize::BITS - upper.leading_zeros();
        loop {
            let value = if bits <= 32 {
                (self.next_u32() >> (32 - bits)) as usize
            } else {
                let low = self.next_u32() as u64;
                let high = (self.next_u32() >> (64 - bits)) as u64;
                (low | (high << 32)) as usize
            };
            if value < upper {
                return value;
            }
        }
    }

    pub fn shuffle<T>(&mut self, values: &mut [T]) {
        for i in (1..values.len()).rev() {
            let selected = self.randbelow(i + 1);
            values.swap(i, selected);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::Value;

    #[test]
    fn cpython_integer_seed_vectors() {
        let golden: Value = serde_json::from_str(include_str!(
            "../../go-backend/internal/pyrandom/testdata/python_random.json"
        ))
        .unwrap();
        for (index, vector) in golden["vectors"].as_array().unwrap().iter().enumerate() {
            let seed = vector["seed"].as_str().unwrap();
            let checkpoints = vector["outputs"].as_array().unwrap();
            let mut rng = Random::from_decimal(seed).unwrap();
            let mut checkpoint = 0;
            let last = checkpoints.last().unwrap()["index"].as_u64().unwrap();
            for i in 0..=last {
                let value = rng.next_u32();
                if i == checkpoints[checkpoint]["index"].as_u64().unwrap() {
                    assert_eq!(
                        u64::from(value),
                        checkpoints[checkpoint]["value"].as_u64().unwrap(),
                        "vector {index}: output {i}"
                    );
                    checkpoint += 1;
                }
            }
            let mut rng = Random::from_decimal(seed).unwrap();
            for (width, expected) in vector["bits"]
                .as_array()
                .unwrap()
                .iter()
                .zip(vector["bit_values"].as_array().unwrap())
            {
                let width = usize::try_from(width.as_u64().unwrap()).unwrap();
                assert_eq!(
                    rng.getrandbits(width).to_string(),
                    expected.as_str().unwrap(),
                    "vector {index}: getrandbits({width})"
                );
            }
            let mut rng = Random::from_decimal(seed).unwrap();
            for (upper, expected) in vector["ranges"]
                .as_array()
                .unwrap()
                .iter()
                .zip(vector["below"].as_array().unwrap())
            {
                let upper = usize::try_from(upper.as_u64().unwrap()).unwrap();
                assert_eq!(
                    rng.randbelow(upper) as u64,
                    expected.as_u64().unwrap(),
                    "vector {index}: randbelow({upper})"
                );
            }
            let mut rng = Random::from_decimal(seed).unwrap();
            let expected: Vec<usize> = vector["shuffle"]
                .as_array()
                .unwrap()
                .iter()
                .map(|value| value.as_u64().unwrap() as usize)
                .collect();
            let mut actual: Vec<usize> = (0..expected.len()).collect();
            rng.shuffle(&mut actual);
            assert_eq!(actual, expected, "vector {index}: shuffle");
        }
    }

    #[test]
    fn zero_bits_does_not_consume_state() {
        let mut left = Random::from_u64(42);
        let mut right = Random::from_u64(42);
        assert_eq!(left.getrandbits(0), BigUint::default());
        assert_eq!(left.next_u32(), right.next_u32());
    }

    #[test]
    fn integer_seed_is_not_mutated() {
        let seed = BigInt::from(-123_456_789);
        let _ = Random::new(&seed);
        assert_eq!(seed, BigInt::from(-123_456_789));
    }
}
