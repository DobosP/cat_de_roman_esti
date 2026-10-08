// Local retry identity; opaque IDs retain their complete JSON string encoding.
export const selectionKey = (ids: readonly string[]) => JSON.stringify([...ids].sort());
