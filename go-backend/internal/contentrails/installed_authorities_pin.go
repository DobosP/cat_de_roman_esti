package contentrails

// This authority metadata is checked separately from the runtime audit manifest:
// including its own review/audit descriptors in that manifest would be circular.
// A changed pin never grants approval; every registered rail is reconstructed
// from its exact independent judgments and current native audit by Check.
const InstalledAuthoritiesSHA256 = "9b794e3879f61e65a2f3e18869b9e013b043c6933e4595d377434a822ad49f03"
