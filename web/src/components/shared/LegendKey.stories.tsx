import type { Meta, StoryObj } from '@storybook/react';
import { LegendKey } from './LegendKey';
import type { Unit } from '../../types';

const meta = {
  title: 'Components/LegendKey',
  component: LegendKey,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: 'Displays footnotes and abbreviations used in the roster sheet. Automatically detects which abbreviations are needed based on the units provided.',
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    className: {
      control: 'text',
      description: 'Additional CSS class names',
    },
  },
} satisfies Meta<typeof LegendKey>;

export default meta;
type Story = StoryObj<typeof meta>;

// Sample units for testing abbreviation detection
const unitsWithVariousAbbrevs: Unit[] = [
  {
    name: "Longstreet",
    size: "Corps",
    command: "Lee",
    type: "Infantry",
    manpowerValue: "24",
    hexLocation: "S5510",
    notes: [],
    tableName: "Confederate Set-Up",
  },
  {
    name: "Jackson",
    size: "Corps",
    command: "Lee",
    type: "Infantry",
    manpowerValue: "18",
    hexLocation: "S5520",
    notes: [],
    tableName: "Inc 1",
    reinforcementSet: "Set 1",
  },
  {
    name: "Stuart",
    size: "Cav",
    command: "Lee",
    type: "Cavalry",
    manpowerValue: "6",
    hexLocation: "S5530",
    notes: [],
    tableName: "Stuart",
  },
  {
    name: "PA Militia",
    size: "Brigade",
    command: "-",
    type: "Infantry",
    manpowerValue: "4",
    hexLocation: "S5540",
    notes: [],
    tableName: "PA Mil",
  },
];

// Stories
export const NoFootnotesOrAbbreviations: Story = {
  args: {
    footnotes: {},
    units: [
      {
        name: "Test Unit",
        size: "Corps",
        command: "Leader",
        type: "Infantry",
        manpowerValue: "10",
        hexLocation: "S5510",
        notes: [],
        tableName: "Confederate Set-Up",
      },
    ],
  },
};

export const OnlyFootnotes: Story = {
  args: {
    footnotes: {
      '*': 'Start at Fatigue Level 2',
      '^': 'Reduced strength',
      '†': 'Elite unit',
    },
    units: [
      {
        name: "Test Unit",
        size: "Corps",
        command: "Leader",
        type: "Infantry",
        manpowerValue: "10",
        hexLocation: "S5510",
        notes: [],
        tableName: "Confederate Set-Up",
      },
    ],
  },
};

export const OnlyAbbreviations: Story = {
  args: {
    footnotes: {},
    units: unitsWithVariousAbbrevs,
  },
};

export const FootnotesAndAbbreviations: Story = {
  args: {
    footnotes: {
      '*': 'Start at Fatigue Level 2',
      '^': 'Reduced strength',
      '†': 'Elite unit',
      '‡': 'Cannot move on first turn',
      '§': 'May not stack',
    },
    units: unitsWithVariousAbbrevs,
  },
};

export const SingleFootnote: Story = {
  args: {
    footnotes: {
      '*': 'All units start at Fatigue Level 1',
    },
    units: [
      {
        name: "Test Unit",
        size: "Corps",
        command: "Leader",
        type: "Infantry",
        manpowerValue: "10",
        hexLocation: "S5510",
        notes: [],
        tableName: "Confederate Set-Up",
      },
    ],
  },
};

export const ManyFootnotes: Story = {
  args: {
    footnotes: {
      '*': 'Start at Fatigue Level 2',
      '^': 'Reduced strength',
      '†': 'Elite unit',
      '‡': 'Cannot move on first turn',
      '§': 'May not stack',
      '$': 'Special movement rules',
      '+': 'Receives reinforcements',
    },
    units: [
      {
        name: "Test Unit",
        size: "Corps",
        command: "Leader",
        type: "Infantry",
        manpowerValue: "10",
        hexLocation: "S5510",
        notes: [],
        tableName: "Confederate Set-Up",
      },
    ],
  },
};

export const WithCustomClassName: Story = {
  args: {
    footnotes: {
      '*': 'Start at Fatigue Level 2',
      '^': 'Reduced strength',
    },
    units: unitsWithVariousAbbrevs,
    className: 'custom-legend-class',
  },
};
