package contentrails

// This authority metadata is checked separately from the runtime audit manifest:
// including its own review/audit descriptors in that manifest would be circular.
// A changed pin never grants approval; every registered rail is reconstructed
// from its exact independent judgments and current native audit by Check.
const InstalledAuthoritiesSHA256 = "4678f753b7bd85d4769d36742083ab4bf4c341d872d3785b98e0cc2027a82131"
