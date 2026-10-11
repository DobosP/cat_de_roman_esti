package contentrails

// This authority metadata is checked separately from the runtime audit manifest:
// including its own review/audit descriptors in that manifest would be circular.
// A changed pin never grants approval; every registered rail is reconstructed
// from its exact independent judgments and current native audit by Check.
const InstalledAuthoritiesSHA256 = "295a4cc68a25a248a15e06c1f71ea7827f2292e07944d8b990032445a718e5ed"
