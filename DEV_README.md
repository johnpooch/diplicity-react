# Getting started with the development of the project

## Component structure

Most component represent either a screen or some reusable UI element. Often, the
component accesses data from global state (Redux). This means that the component
is a **connected** component.

**Connected** components usually have the following structure:

- A React component, e.g. `Channel`, which is the UI element. The component
  should not directly contain any business logic. It should only include
  rendering logic.

- A **custom hook** which is used to access the global state. This hook might be
  called `useChannel`. It hides away the details of how global state is
  accessed. (Note, by using a custom hook, we can easily share business logic
  between web and native implementations.)

- A **mergeQueries** call might appear inside the custom hook. This is used to
  combine multiple queries into a single query. A lot of our application logic
  depends on data that is merged from multiple separate queries.

The important thing to remember is that the React component should be as simple
as possible and that all business logic should be added to custom hooks or
pushed as high up as possible, e.g. schemas, etc.

## Schemas

Schemas live in `src/common/schema`. They are used for the following:

- Validate that the data that is returned from the server has the expected type.
- Provide types to the rest of the application.
- Perform initial transformations to data that is returned from the server.

We perform transformations at the schema level to ensure that the data is in the
desired format for the entire application.

For example, many `Variant` objects do not have a flag for every nation. We know
that in this scenario, we want to use the default flags from the `Classical`
variant. Rather than building that logic into every component that needs it,
we can build it into the schema transformation.

See `src/common/schema/list-variants.ts`.
