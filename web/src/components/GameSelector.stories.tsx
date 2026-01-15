import type { Meta, StoryObj } from '@storybook/react';
import { GameSelector } from './GameSelector';
import type { GameInfo } from '../types';

const meta = {
  title: 'Components/GameSelector',
  component: GameSelector,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'A dropdown selector for choosing a GCACW game. Hidden when printing.',
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    selectedGameId: {
      control: 'text',
      description: 'The ID of the currently selected game',
    },
    onSelect: { action: 'game selected' },
  },
} satisfies Meta<typeof GameSelector>;

export default meta;
type Story = StoryObj<typeof meta>;

// Sample game data
const sampleGames: GameInfo[] = [
  { id: 'otr2', name: 'On To Richmond! 2nd Ed', file: 'otr2.json' },
  { id: 'gtc2', name: 'Grant Takes Command 2nd Ed', file: 'gtc2.json' },
  { id: 'hsn2', name: 'Hood Strikes North 2nd Ed', file: 'hsn2.json' },
  { id: 'hctr2', name: 'Here Come the Rebels! 2nd Ed', file: 'hctr2.json' },
  { id: 'rtg2', name: 'Roads to Gettysburg 2nd Ed', file: 'rtg2.json' },
];

// Stories
export const NoSelection: Story = {
  args: {
    games: sampleGames,
    selectedGameId: null,
  },
};

export const GameSelected: Story = {
  args: {
    games: sampleGames,
    selectedGameId: 'gtc2',
  },
};

export const SingleGame: Story = {
  args: {
    games: [sampleGames[0]],
    selectedGameId: null,
  },
};

export const ManyGames: Story = {
  args: {
    games: [
      ...sampleGames,
      { id: 'ritwh', name: 'Rebels in the White House', file: 'ritwh.json' },
      { id: 'test1', name: 'Test Game 1', file: 'test1.json' },
      { id: 'test2', name: 'Test Game 2', file: 'test2.json' },
    ],
    selectedGameId: 'hsn2',
  },
};
