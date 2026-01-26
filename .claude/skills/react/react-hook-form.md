# React Hook Form Best Practices

## Relationship with react-zod Guidance

**This File (react-hook-form):**
- Focuses on form state management and React Hook Form patterns
- Covers form submission, field registration, and form utilities
- Addresses prop drilling, performance optimization, and error handling within forms

**react-zod File:**
- Focuses on schema validation and type safety with Zod
- Covers API response validation and data parsing patterns
- Includes React Hook Form integration specifically for validation schemas

**When Both Apply:**
- For forms with complex validation, both files provide recommendations
- react-hook-form for form structure and state management
- react-zod for schema definition and validation integration

## Key Principles

### 1. Use React Hook Form for Form State Management

**Issue:** Manual handling of form state, validation, and submission creates unnecessary complexity
**Solution:** Leverage React Hook Form to eliminate boilerplate code

```tsx
// ❌ Before - Manual state management
const [firstNameValue, setFirstNameValue] = useState("");
const [firstNameValueInvalid, setFirstNameValueInvalid] = useState(false);
const [isSubmitting, setIsSubmitting] = useState(false);

const handleSubmit = async (e) => {
  e.preventDefault();
  setIsSubmitting(true);

  if (!firstNameValue) {
    setFirstNameValueInvalid(true);
    setIsSubmitting(false);
    return;
  }

  // ... submit logic
  setIsSubmitting(false);
};

// ✅ After - Using React Hook Form
import { useForm } from "react-hook-form";
import { ErrorMessage } from "@hookform/error-message"

const {
  register,
  handleSubmit,
  formState: { isSubmitting, errors },
} = useForm();

const onSubmit = async (data) => {
  // RHF handles preventDefault and submission state automatically
  // ... submit logic
};

return (
  <form onSubmit={handleSubmit(onSubmit)}>
    <input {...register("firstName", { required: "This is required." })} />
    <ErrorMessage errors={errors} name="firstName" />

    <button disabled={isSubmitting}>Submit</button>
  </form>
);
```

**Rationale:** React Hook Form removes the need for manual validation, submission handling, and state management

### 2. Integrate Zod Schema for Validation (When Appropriate)

**When to Use Zod with React Hook Form:**
- When forms map closely to API request/response schemas
- When you need to share validation logic between frontend and backend
- When forms have complex validation requirements
- When type safety is critical for form data

**When Plain React Hook Form May Suffice:**
- Simple forms with basic validation
- Forms that don't correspond to API schemas
- One-off forms with unique validation logic

```tsx
// ❌ Before - Inline validation
const validate = (value) => {
  if (!value) return "Required";
  if (value.length < 3) return "Too short";
  return true;
};

// ✅ After - Using Zod with resolver (you have @hookform/resolvers installed)
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

const schema = z.object({
  name: z.string().min(3, "Too short").max(100),
  email: z.string().email(),
});

const { register, handleSubmit } = useForm({
  resolver: zodResolver(schema),
});
```

**Rationale:** Centralized schema validation provides type safety and reusability

### 3. Use Built-in formState Instead of Custom State

**Issue:** Creating custom state variables for form submission states
**Solution:** Utilize React Hook Form's formState object

```tsx
// ❌ Before - Custom state
const [isSaving, setIsSaving] = useState(false);

const handleSubmit = async (data) => {
  setIsSaving(true);
  await saveData(data);
  setIsSaving(false);
};

// ✅ After - Using formState
const {
  handleSubmit,
  formState: { isSubmitting },
} = useForm();

const onSubmit = async (data) => {
  // isSubmitting automatically managed by RHF
  await saveData(data);
};

return (
  <button disabled={isSubmitting}>{isSubmitting ? "Saving..." : "Save"}</button>
);
```

**Rationale:** React Hook Form automatically manages submission state, reducing code complexity

### 4. Optimize Field Watching for Performance

**Issue:** Watching all form fields unnecessarily can impact performance
**Solution:** Watch only specific fields needed or use useWatch in child components

```tsx
// ❌ Before - Watching all fields
const watchedValues = watch();

// ✅ After - Watching specific fields
const [field1, field2] = watch(["field1", "field2"]);

// Or using useWatch in child component
import { useWatch } from "react-hook-form";

function ChildComponent() {
  const watchedValues = useWatch({
    name: ["field1", "field2"],
  });
}
```

**Rationale:** Selective watching prevents unnecessary re-renders and improves performance

### 5. Use Reset Method for Form Reset

**Issue:** Manually resetting form fields one by one
**Solution:** Use React Hook Form's reset method

```tsx
// ❌ Before - Manual reset
const handleReset = () => {
  setField1("");
  setField2("");
  setField3("");
};

// ✅ After - Using reset
const { reset } = useForm();

const handleReset = () => {
  reset(); // Reset to default values
  // or
  reset(newValues); // Reset to specific values
};
```

**Rationale:** The reset method provides a clean way to reset forms with options for default or custom values

### 6. Handle Form-Level Errors Appropriately

**Issue:** Need to display form-level errors vs field-specific errors
**Solution:** Use formState.errors and consider ErrorMessage component for field errors

```tsx
// For field-specific errors
import { ErrorMessage } from "@hookform/error-message";

<ErrorMessage
  errors={errors}
  name="fieldName"
  render={({ message }) => <p className="text-red-500">{message}</p>}
/>;

// For form-level errors
const getFormError = (errors) => {
  // Custom utility to extract first error for form-level display
  const firstError = Object.values(errors)[0];
  return firstError?.message;
};
```

**Rationale:** Different error display strategies suit different UX needs

### 7. Leverage Built-in Event Handling

**Issue:** Manually calling preventDefault on form submission
**Solution:** React Hook Form's handleSubmit automatically handles preventDefault

```tsx
// ❌ Before - Manual preventDefault
const onSubmit = (e) => {
  e.preventDefault();
  // handle submission
};

// ✅ After - RHF handles it
const { handleSubmit } = useForm();

<form onSubmit={handleSubmit(onSubmit)}>
  {/* preventDefault is handled automatically */}
</form>;
```

**Rationale:** React Hook Form handles common form behaviors internally, reducing boilerplate

## Integration with Material UI / Radix UI

Since the project uses both Material UI (transitioning away) and Radix UI:

### Material UI Integration
```tsx
import { TextField } from '@mui/material';
import { Controller } from 'react-hook-form';

<Controller
  name="firstName"
  control={control}
  rules={{ required: "This field is required" }}
  render={({ field, fieldState: { error } }) => (
    <TextField
      {...field}
      error={!!error}
      helperText={error?.message}
    />
  )}
/>
```

### Radix UI Integration (Preferred for new components)
```tsx
import * as Label from '@radix-ui/react-label';

<div>
  <Label.Root htmlFor="firstName">First Name</Label.Root>
  <input
    id="firstName"
    {...register("firstName", { required: "This field is required" })}
    className="border rounded px-2 py-1"
  />
  {errors.firstName && (
    <span className="text-red-500 text-sm">{errors.firstName.message}</span>
  )}
</div>
```

## Migration Tips for Formik Users

Since the project has Formik installed but should migrate to React Hook Form:

1. **Replace useFormik with useForm**
2. **Convert Formik Field to register**
3. **Replace Formik validation with Zod schemas**
4. **Use formState instead of Formik's isSubmitting**
5. **Replace Formik's ErrorMessage with @hookform/error-message**

## Common Pitfalls to Avoid

1. **Creating custom submission state** when formState.isSubmitting is available
2. **Watching all fields** when only specific fields are needed
3. **Manual form reset** instead of using the reset method
4. **Ignoring built-in validation** in favor of custom validation logic
5. **Not leveraging resolvers** for schema validation with Zod (you have zod-formik-adapter but should use @hookform/resolvers)

## TypeScript Best Practices

```tsx
// Define form data type from Zod schema
import { z } from 'zod';

const formSchema = z.object({
  firstName: z.string().min(1),
  email: z.string().email(),
});

type FormData = z.infer<typeof formSchema>;

// Use with useForm
const { register, handleSubmit } = useForm<FormData>({
  resolver: zodResolver(formSchema),
});
```

## Resources

- [React Hook Form Documentation](https://react-hook-form.com/)
- [React Hook Form with Zod](https://react-hook-form.com/get-started#SchemaValidation)
- [useForm API](https://react-hook-form.com/docs/useform)
- [formState API](https://react-hook-form.com/docs/useform/formstate)
- [ErrorMessage Component](https://react-hook-form.com/docs/useformstate/errormessage)

## Summary

React Hook Form significantly reduces form complexity by:

- Eliminating manual state management
- Providing built-in validation integration
- Offering performance optimizations
- Reducing boilerplate code
- Improving developer experience

Adopting these patterns leads to more maintainable, performant, and consistent form implementations across the codebase.