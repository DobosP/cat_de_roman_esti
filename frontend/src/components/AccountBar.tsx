import AccountBarContents from "./AccountBarContents";

const CURRENT_YEAR = new Date().getFullYear();

export default function AccountBar() {
  return <AccountBarContents currentYear={CURRENT_YEAR} />;
}
