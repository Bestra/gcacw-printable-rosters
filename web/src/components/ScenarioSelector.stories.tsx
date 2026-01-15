import type { Meta, StoryObj } from '@storybook/react';
import { ScenarioSelector } from './ScenarioSelector';
import type { Scenario } from '../types';

const meta = {
  title: 'Components/ScenarioSelector',
  component: ScenarioSelector,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'A dropdown selector for choosing a scenario within a game. Hidden when printing.',
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    selectedNumber: {
      control: 'number',
      description: 'The number of the currently selected scenario',
    },
    onSelect: { action: 'scenario selected' },
  },
} satisfies Meta<typeof ScenarioSelector>;

export default meta;
type Story = StoryObj<typeof meta>;

// Sample scenario data
const sampleScenarios: Scenario[] = [
  {
    number: 1,
    name: 'The Siege Begins',
    confederateFootnotes: {},
    unionFootnotes: {},
    confederateUnits: [],
    unionUnits: [],
    confederateGunboats: [],
    unionGunboats: [],
  },
  {
    number: 2,
    name: 'First Day at Shiloh',
    confederateFootnotes: {},
    unionFootnotes: {},
    confederateUnits: [],
    unionUnits: [],
    confederateGunboats: [],
    unionGunboats: [],
  },
  {
    number: 3,
    name: 'The Sunken Road',
    confederateFootnotes: {},
    unionFootnotes: {},
    confederateUnits: [],
    unionUnits: [],
    confederateGunboats: [],
    unionGunboats: [],
  },
  {
    number: 4,
    name: 'Grant\'s Counterattack',
    confederateFootnotes: {},
    unionFootnotes: {},
    confederateUnits: [],
    unionUnits: [],
    confederateGunboats: [],
    unionGunboats: [],
  },
];

// Stories
export const NoSelection: Story = {
  args: {
    scenarios: sampleScenarios,
    selectedNumber: null,
  },
};

export const ScenarioSelected: Story = {
  args: {
    scenarios: sampleScenarios,
    selectedNumber: 2,
  },
};

export const SingleScenario: Story = {
  args: {
    scenarios: [sampleScenarios[0]],
    selectedNumber: null,
  },
};

export const ManyScenarios: Story = {
  args: {
    scenarios: [
      ...sampleScenarios,
      {
        number: 5,
        name: 'The Full Campaign',
        confederateFootnotes: {},
        unionFootnotes: {},
        confederateUnits: [],
        unionUnits: [],
        confederateGunboats: [],
        unionGunboats: [],
      },
      {
        number: 6,
        name: 'Alternative History',
        confederateFootnotes: {},
        unionFootnotes: {},
        confederateUnits: [],
        unionUnits: [],
        confederateGunboats: [],
        unionGunboats: [],
      },
    ],
    selectedNumber: 4,
  },
};
