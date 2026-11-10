package contentrails

// This authority metadata is checked separately from the runtime audit manifest:
// including its own review/audit descriptors in that manifest would be circular.
// A changed pin never grants approval; every registered rail is reconstructed
// from its exact independent judgments and current native audit by Check.
const InstalledAuthoritiesSHA256 = "75a04b144425c50c62a152d05fe6663186902f4ebb45e7e7f95bbb6621d05a7b"
