package contentrails

// This authority metadata is checked separately from the runtime audit manifest:
// including its own review/audit descriptors in that manifest would be circular.
// A changed pin never grants approval; every registered rail is reconstructed
// from its exact independent judgments and current native audit by Check.
const InstalledAuthoritiesSHA256 = "2968526063e3e483e55f0a9186bdf98f5ce68ea954c064d46b542c3fc08914d7"
