import type { Meta, StoryObj } from '@storybook/react';
import { UnitCard } from './UnitCard';
import type { Unit } from '../types';

const meta = {
  title: 'Components/UnitCard',
  component: UnitCard,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: 'A card component that displays a single unit with three counter boxes: unit counter, leader/MP info, and hex/fatigue info. Sized at 0.55" to fit GCACW\'s 1/2" counters.',
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    side: {
      control: 'radio',
      options: ['confederate', 'union'],
      description: 'The side/faction the unit belongs to',
    },
    empty: {
      control: 'boolean',
      description: 'Whether to show an empty card placeholder',
    },
    showImages: {
      control: 'boolean',
      description: 'Whether to show unit counter images',
    },
  },
} satisfies Meta<typeof UnitCard>;

export default meta;
type Story = StoryObj<typeof meta>;

// Sample unit data
const sampleConfederateUnit: Unit = {
  name: "Longstreet",
  size: "Corps",
  command: "Lee",
  type: "Infantry",
  manpowerValue: "24",
  hexLocation: "S5510 (Yorktown)",
  notes: ["*"],
  tableName: "Confederate Set-Up",
};

const sampleUnionUnit: Unit = {
  name: "II Corps",
  size: "Corps",
  command: "McClellan",
  type: "Infantry",
  manpowerValue: "32",
  hexLocation: "S5520",
  notes: ["^", "†"],
  tableName: "Union Set-Up",
};

const unitWithReinforcement: Unit = {
  name: "Jackson",
  size: "Corps",
  command: "Lee",
  type: "Infantry",
  manpowerValue: "18",
  hexLocation: "S5530",
  notes: [],
  reinforcementSet: "Set 2",
  tableName: "Confederate Reinforcements",
};

const specialUnit: Unit = {
  name: "Wagon Train",
  size: "-",
  command: "-",
  type: "Special",
  manpowerValue: "-",
  hexLocation: "S5540",
  notes: [],
  tableName: "Confederate Set-Up",
};

// Stories
export const Empty: Story = {
  args: {
    empty: true,
  },
};

export const ConfederateDefault: Story = {
  args: {
    unit: sampleConfederateUnit,
    side: 'confederate',
    gameId: 'gtc2',
    showImages: false,
  },
};

export const ConfederateWithLeader: Story = {
  args: {
    unit: sampleConfederateUnit,
    side: 'confederate',
    leaderName: '[Lee]',
    gameId: 'gtc2',
    showImages: false,
  },
};

export const ConfederateWithFatigue: Story = {
  args: {
    unit: sampleConfederateUnit,
    side: 'confederate',
    startingFatigue: 'FL2',
    gameId: 'gtc2',
    showImages: false,
  },
};

export const UnionDefault: Story = {
  args: {
    unit: sampleUnionUnit,
    side: 'union',
    gameId: 'gtc2',
    showImages: false,
  },
};

export const UnionWithLeaderAndFatigue: Story = {
  args: {
    unit: sampleUnionUnit,
    side: 'union',
    leaderName: 'McClellan',
    startingFatigue: 'FL1',
    gameId: 'gtc2',
    showImages: false,
  },
};

export const ReinforcementUnit: Story = {
  args: {
    unit: unitWithReinforcement,
    side: 'confederate',
    gameId: 'gtc2',
    showImages: false,
  },
};

export const SpecialUnit: Story = {
  args: {
    unit: specialUnit,
    side: 'confederate',
    gameId: 'gtc2',
    showImages: false,
  },
};

export const WithImages: Story = {
  args: {
    unit: sampleConfederateUnit,
    side: 'confederate',
    gameId: 'gtc2',
    showImages: true,
  },
  parameters: {
    docs: {
      description: {
        story: 'Shows unit card with counter images enabled. Note: Images may not display in Storybook without proper base path configuration.',
      },
    },
  },
};
