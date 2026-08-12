# React Component Best Practices

Evaluate the code against the following rules:

- **MANDATORY**: Always check existing components in `src/components/` before creating new ones
- If a similar component exists, extend or modify it rather than creating duplicates
- Use Radix UI primitives for new base components (you already have many @radix-ui packages installed)
- For complex UI, consider shadcn/ui patterns as inspiration (without directly copying)
- Break down components larger than 200 lines
- Use compound component patterns for complex components
- Co-locate related components in the same directory
- We use React 19
- **PREFER**: Avoid custom memoization (`useMemo`, `useCallback`) - React 19 handles this automatically in most cases
- **EXCEPTION - Third-party hooks with reference equality**: Some third-party hooks rely on reference equality for their arguments. When using these hooks, you MUST:
  1. Explicitly memoize their arguments (data, columns, options, etc.) with `useMemo`/`useCallback`
  - **Known cases**: TanStack Table (`useReactTable`), TanStack Virtual (`useVirtualizer`)
  - **How to identify**: If a hook creates new instances or behaves incorrectly when props/state change, it likely relies on reference equality

## React 19 Context Usage

In React 19, Context objects can be rendered directly as providers without using the `.Provider` property.

**✅ DO: Render Context directly**

```tsx
export const ThemeContext = createContext<Theme | null>(null);

export const ThemeProvider = ({ children }: PropsWithChildren) => {
  const [theme, setTheme] = useState<Theme>('light');
  return <ThemeContext value={{ theme, setTheme }}>{children}</ThemeContext>;
};
```

**❌ DON'T: Use deprecated `.Provider` syntax**

```tsx
// This is deprecated in React 19
return <ThemeContext.Provider value={{ theme, setTheme }}>{children}</ThemeContext.Provider>;
```

**Why:** React 19 simplified the Context API by making Context objects renderable directly as providers. The `.Provider` property is deprecated and will be removed in future React versions.

**Reference:** [React 19 Release - Context as a Provider](https://react.dev/blog/2024/12/05/react-19#context-as-a-provider)

## React 19 Ref Handling

In React 19, never use `forwardRef` - always pass `ref` as a regular prop instead.

**✅ DO: Pass ref as a regular prop**

```tsx
interface ButtonProps {
  ref?: React.Ref<HTMLButtonElement>;
  children: React.ReactNode;
}

function Button({ ref, children }: ButtonProps) {
  return <button ref={ref}>{children}</button>;
}
```

**❌ DON'T: Use forwardRef (deprecated in React 19)**

```tsx
// This pattern is no longer needed in React 19
const Button = forwardRef<HTMLButtonElement, ButtonProps>((props, ref) => {
  return <button ref={ref}>{props.children}</button>;
});
```

## TypeScript Best Practices

- **Never use `any`** - always provide proper types
- **Use interface for props** instead of type when possible
- **Export prop interfaces** for reusability
- **Use generic components** when appropriate

```tsx
interface DataTableProps<T> {
  data: T[];
  columns: Column<T>[];
  onRowClick?: (row: T) => void;
}

export function DataTable<T>({ data, columns, onRowClick }: DataTableProps<T>) {
  // Implementation
}
```

## Performance Considerations

1. **Code splitting**: Use lazy loading for large components

   ```tsx
   const GameBoard = lazy(() => import('./GameBoard'));
   ```

2. **Virtualization**: Use `@tanstack/react-virtual` for large lists

3. **Image optimization**: Use appropriate image formats and lazy loading

4. **Bundle size**: Monitor component dependencies and avoid importing entire libraries

## Testing Guidelines

- Write tests alongside components in `.test.tsx` files
- Use Testing Library patterns (you have @testing-library/react installed)
- Focus on user interactions rather than implementation details
- Mock API calls with MSW (you have msw installed)
