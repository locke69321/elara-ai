declare namespace JSX {
  type Element = unknown

  interface IntrinsicElements {
    [elementName: string]: Record<string, unknown>
  }
}

declare module 'react/jsx-runtime' {
  export const Fragment: unique symbol

  export function jsx(
    type: unknown,
    props: Record<string, unknown>,
    key?: string,
  ): JSX.Element

  export function jsxs(
    type: unknown,
    props: Record<string, unknown>,
    key?: string,
  ): JSX.Element
}

declare module '@tanstack/react-router' {
  type RouteComponent = () => JSX.Element

  export function createRootRoute(options: { component: RouteComponent }): unknown

  export function createFileRoute(
    path: string,
  ): (options: { component: RouteComponent }) => unknown

  export function Link(props: {
    key?: string
    to: string
    className?: string
    children?: unknown
  }): JSX.Element

  export function Outlet(): JSX.Element
}

declare module '@tanstack/react-start' {
  type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'

  export function createServerFn(options: { method: HttpMethod }): {
    handler<TArgs = void, TResult = void>(
      fn: (args: TArgs) => TResult | Promise<TResult>,
    ): (args: TArgs) => Promise<TResult>
  }
}

declare module '*.css'
