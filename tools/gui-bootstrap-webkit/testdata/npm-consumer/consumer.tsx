import { createRef, type ComponentChild } from 'preact';
import { Button as RootButton, useCspSafeStyle, type CspStyleInput, createApiClient as rootClient } from '@roedu/ui';
import {
  Button, Card, Stack, Container, Field, Input, Select, Checkbox, Radio, Dialog, Tabs,
  Badge, Spinner, Skeleton, ErrorBoundary, ToastHost, ReadingComfortBar,
  type ButtonProps, type FieldControlProps,
} from '@roedu/ui/preact';
import { Presence, Confetti, useIsPresent, animateHeight, springs, motionAllowed } from '@roedu/ui/motion';
import { define, loadIslands, invokeCommand, installInvokerShim, type IslandModule, type IslandContext } from '@roedu/ui/behaviors';
import { csrfFetch, createApiClient, ApiError, csrf, type RoeduApiClient } from '@roedu/ui/net';
import { storageKeys, registerStorageKey, readStored, writeStored } from '@roedu/ui/storage';
import '@roedu/ui/styles.css';
import '@roedu/ui/tokens.css';
import '@roedu/ui/theme-cat.css';
import '@roedu/ui/theme-teacher.css';
import '@roedu/ui/theme-social.css';

const buttonRef = createRef<HTMLButtonElement>();
const inputRef = createRef<HTMLInputElement>();
const signal = new AbortController().signal;
const buttonProps: ButtonProps = { variant: 'secondary', size: 'sm', ref: buttonRef, 'aria-label': 'Continue', onClick(event) { event.currentTarget.focus(); } };
const cspStyle: CspStyleInput = { '--roedu-consumer-probe': '13px' };

export function Consumer(): ComponentChild {
  const present: boolean = useIsPresent();
  const ref = useCspSafeStyle<HTMLDivElement>(cspStyle);
  return <ErrorBoundary fallback={<p>Recovered</p>}>
    <Container ref={ref} maxWidth={960}><Stack gap="sm" direction="column">
      <Card interactive><RootButton {...buttonProps}>Root surface</RootButton><Button {...buttonProps}>Preact surface</Button></Card>
      <Field label="Name" hint="Visible guidance">{(props: FieldControlProps) => <Input {...props} ref={inputRef} label="Name" required />}</Field>
      <Select label="Choice" options={[{ value: 'one', label: 'One' }]} />
      <Checkbox label="Agreed" checked /><Radio label="First" name="choice" value="one" />
      <Dialog open={false} title="Details" description="Controlled dialog" onClose={() => undefined}><Button>Close</Button></Dialog>
      <Tabs label="Sections" items={[{ id:'one', label:'One', content:<p>First</p> }]} />
      <Badge tone="success">Saved</Badge><Spinner label="Loading" /><Skeleton width="10rem" height="2rem" />
      <ToastHost toasts={[{id:1,kind:'info',message:'Saved'}]} onDismiss={(id: number) => { void id; }} />
      <ReadingComfortBar surface="self-paced" />
      <Presence mode="wait" initial={false}><p key="present">{present ? 'Present' : 'Exiting'}</p></Presence>
      <Confetti count={8} durationMs={120} />
    </Stack></Container>
  </ErrorBoundary>;
}

export function typedControls(element: HTMLElement): void {
  const height = animateHeight(element, 0, 'auto', springs.gentle);
  height.stop(); height.cancel(); height.complete();
  const allowed: boolean = motionAllowed(element); void allowed;
  const api: RoeduApiClient = createApiClient({baseUrl:'/api'});
  const response: Promise<{count:number}> = api.get<{count:number}>('/count',{signal}); void response;
  const posted: Promise<{saved:boolean}> = rootClient({baseUrl:'/api'}).post<{saved:boolean}>('/save',{value:1},{signal}); void posted;
  const fetched: Promise<Response> = csrfFetch('/save',{method:'POST',signal}); void fetched;
  const error = new ApiError('Fixture',400,{code:'invalid'}); const status: number = error.status; void status;
  const header: 'X-CSRFToken' = csrf.header; void header;
  const key: string = registerStorageKey('roedu-consumer-fixture');
  const value: {count:number} = readStored(key,{count:0});
  const written: boolean = writeStored(key,value); void written; void storageKeys.readingComfort;
  const module: IslandModule = { mount(root: Element, props: unknown, context: IslandContext) { void props;void context.signal;void context.nonce;return () => root.replaceChildren(); } };
  const dispose: () => void = loadIslands({fixture:async()=>module},document,'fixture-nonce'); dispose();
  define(); const uninstall: () => void = installInvokerShim(); uninstall();
  if (buttonRef.current) invokeCommand(buttonRef.current);
}

// These fail if a published declaration silently becomes any or loses its
// safety/DOM constraints. No ambient wildcard or source alias is installed.
// @ts-expect-error unsupported button variant
const wrongVariant = <Button variant="not-a-variant" />;
// @ts-expect-error wrong native ref target
const wrongRef = <Button ref={inputRef} />;
// @ts-expect-error unsupported Presence mode
const wrongMode = <Presence mode="serial" />;
// @ts-expect-error reading comfort excludes timed assessment surfaces
const timedComfort = <ReadingComfortBar surface="timed" />;
void wrongVariant; void wrongRef; void wrongMode; void timedComfort;
