# Storybook Documentation

## Overview

This project uses [Storybook](https://storybook.js.org/) for component development and documentation. Storybook provides an isolated environment where you can:

- Develop UI components in isolation
- Document component APIs with interactive controls
- Test different component states and edge cases
- Share component documentation with the team

## Running Storybook

### Development Mode

To start Storybook in development mode with hot-reloading:

```bash
cd web
npm run storybook
```

This will start Storybook at [http://localhost:6006](http://localhost:6006).

### Production Build

To build a static version of Storybook for deployment:

```bash
cd web
npm run build-storybook
```

The static files will be generated in `web/storybook-static/`.

## Available Stories

We currently have stories for the following components:

### 1. UnitCard
**Location:** `src/components/UnitCard.stories.tsx`

Displays a unit with three counter boxes for unit info, leader/MP, and hex/fatigue. Stories include:
- Empty card placeholder
- Confederate and Union variants
- Units with leaders and fatigue levels
- Reinforcement units
- Special units (wagons, gunboats, etc.)
- Units with counter images

### 2. GameSelector
**Location:** `src/components/GameSelector.stories.tsx`

Dropdown selector for choosing a GCACW game. Stories include:
- No selection state
- Game selected state
- Single game
- Multiple games

### 3. ScenarioSelector
**Location:** `src/components/ScenarioSelector.stories.tsx`

Dropdown selector for choosing a scenario within a game. Stories include:
- No selection state
- Scenario selected state
- Single scenario
- Multiple scenarios

### 4. LegendKey
**Location:** `src/components/shared/LegendKey.stories.tsx`

Displays footnotes and abbreviations used in the roster sheet. Stories include:
- Only footnotes
- Only abbreviations
- Both footnotes and abbreviations
- Many footnotes
- Edge cases (empty, single item)

### 5. GunboatsList
**Location:** `src/components/shared/GunboatsList.stories.tsx`

Displays a list of gunboat units with their locations. Stories include:
- Empty list
- Single gunboat
- Multiple gunboats
- Gunboats with/without locations
- Long location names

## Writing New Stories

### Basic Story Structure

Stories are written using the Component Story Format (CSF 3.0). Here's a basic template:

```typescript
import type { Meta, StoryObj } from '@storybook/react';
import { YourComponent } from './YourComponent';

const meta = {
  title: 'Components/YourComponent',  // Category/Name in Storybook UI
  component: YourComponent,
  parameters: {
    layout: 'centered',  // or 'padded', 'fullscreen'
    docs: {
      description: {
        component: 'A brief description of what this component does.',
      },
    },
  },
  tags: ['autodocs'],  // Enable auto-generated documentation
  argTypes: {
    // Define controls for component props
    propName: {
      control: 'text',  // or 'boolean', 'number', 'select', etc.
      description: 'Description of this prop',
    },
  },
} satisfies Meta<typeof YourComponent>;

export default meta;
type Story = StoryObj<typeof meta>;

// Define individual stories
export const Default: Story = {
  args: {
    propName: 'value',
  },
};

export const WithDifferentState: Story = {
  args: {
    propName: 'different value',
  },
};
```

### Best Practices

1. **Create stories for reusable components** - Focus on components that are used in multiple places or have various states.

2. **Show all important states** - Create stories that demonstrate:
   - Default/empty states
   - Loading states
   - Error states
   - Edge cases (long text, many items, etc.)
   - Different prop combinations

3. **Use meaningful story names** - Name stories based on what they demonstrate, not just "Story1", "Story2".

4. **Add documentation** - Use the `parameters.docs.description` field to explain what each story demonstrates.

5. **Keep stories simple** - Each story should focus on demonstrating one specific state or use case.

6. **Use TypeScript** - Stories are written in TypeScript (`.stories.tsx`) for type safety.

### Handling Component Dependencies

If your component uses React Context or other providers, you can wrap it in a decorator:

```typescript
const meta = {
  // ... other config
  decorators: [
    (Story) => (
      <SomeProvider>
        <Story />
      </SomeProvider>
    ),
  ],
} satisfies Meta<typeof YourComponent>;
```

### Action Handlers

For callbacks and event handlers, use Storybook's action feature:

```typescript
const meta = {
  // ... other config
  argTypes: {
    onClick: { action: 'clicked' },
    onChange: { action: 'changed' },
  },
} satisfies Meta<typeof YourComponent>;
```

When you interact with the component in Storybook, these actions will be logged in the Actions panel.

## Storybook Configuration

### Main Configuration
**Location:** `web/.storybook/main.ts`

Defines which files are treated as stories and which addons are enabled.

### Preview Configuration
**Location:** `web/.storybook/preview.ts`

Imports global styles and defines default parameters for all stories.

### Enabled Addons

- **@chromatic-com/storybook** - Visual regression testing
- **@storybook/addon-vitest** - Integration with Vitest
- **@storybook/addon-a11y** - Accessibility testing
- **@storybook/addon-docs** - Auto-generated documentation
- **@storybook/addon-onboarding** - First-time user guide

## Troubleshooting

### Stories not showing up
- Make sure your story file ends with `.stories.tsx` or `.stories.ts`
- Check that the file is in the `src/` directory
- Verify the file exports a default meta object and at least one story

### Styles not loading
- Global styles are imported in `web/.storybook/preview.ts`
- Component-specific CSS files are imported in the component file itself
- Ensure both the component and its CSS are properly imported

### TypeScript errors
- Make sure you're using the correct types from `@storybook/react-vite`
- Run `npm install` to ensure all dependencies are up to date
- Check that your `tsconfig.json` includes the `.storybook` directory if needed

## Further Resources

- [Storybook Documentation](https://storybook.js.org/docs)
- [Component Story Format](https://storybook.js.org/docs/react/api/csf)
- [Writing Stories](https://storybook.js.org/docs/react/writing-stories/introduction)
- [Storybook Addons](https://storybook.js.org/addons)
