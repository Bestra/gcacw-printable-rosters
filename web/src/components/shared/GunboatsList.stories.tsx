import type { Meta, StoryObj } from '@storybook/react';
import { GunboatsList } from './GunboatsList';
import type { Gunboat } from '../../types';

const meta = {
  title: 'Components/GunboatsList',
  component: GunboatsList,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: 'Displays a list of gunboat units with their locations. Returns null if no gunboats are provided.',
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
} satisfies Meta<typeof GunboatsList>;

export default meta;
type Story = StoryObj<typeof meta>;

// Sample gunboat data
const sampleGunboats: Gunboat[] = [
  { name: 'USS Monitor', location: 'Hampton Roads' },
  { name: 'USS Galena', location: 'Drewry\'s Bluff' },
  { name: 'USS Port Royal', location: 'City Point' },
];

// Stories
export const Empty: Story = {
  args: {
    gunboats: [],
  },
};

export const SingleGunboat: Story = {
  args: {
    gunboats: [{ name: 'USS Monitor', location: 'Hampton Roads' }],
  },
};

export const MultipleGunboats: Story = {
  args: {
    gunboats: sampleGunboats,
  },
};

export const GunboatWithoutLocation: Story = {
  args: {
    gunboats: [{ name: 'CSS Virginia', location: '' }],
  },
};

export const MixedLocations: Story = {
  args: {
    gunboats: [
      { name: 'USS Monitor', location: 'Hampton Roads' },
      { name: 'CSS Virginia', location: '' },
      { name: 'USS Galena', location: 'Drewry\'s Bluff' },
    ],
  },
};

export const ManyGunboats: Story = {
  args: {
    gunboats: [
      ...sampleGunboats,
      { name: 'USS Aroostook', location: 'James River' },
      { name: 'USS Naugatuck', location: 'York River' },
      { name: 'USS Maratanza', location: 'Chesapeake Bay' },
      { name: 'USS Sebago', location: 'Pamunkey River' },
    ],
  },
};

export const LongLocationNames: Story = {
  args: {
    gunboats: [
      { name: 'USS Monitor', location: 'Hampton Roads near Fort Monroe at the mouth of the James River' },
      { name: 'USS Galena', location: 'Drewry\'s Bluff defensive position on the James River' },
    ],
  },
};

export const WithCustomClassName: Story = {
  args: {
    gunboats: sampleGunboats,
    className: 'custom-gunboats-class',
  },
};
