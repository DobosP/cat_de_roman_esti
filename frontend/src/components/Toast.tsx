// Toast was promoted into the shared design system (@roedu/ui). This shim keeps the
// old import path alive for screens not yet migrated; import from "@roedu/ui" directly
// in new code. TODO(redesign): delete once all screens import from @roedu/ui.

export type { ToastData, ToastKind } from "@roedu/ui";
export { ToastStack } from "@roedu/ui";
