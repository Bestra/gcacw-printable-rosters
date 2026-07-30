import type { Meta, StoryObj } from "@storybook/react";
import { CommandCard, type CommandCardProps } from "./CommandCard";

const meta = {
  title: "Prototypes/Scenario Command Cards",
  component: CommandCard,
  parameters: {
    layout: "centered",
    backgrounds: {
      default: "table",
      values: [
        { name: "table", value: "#8a836d" },
        { name: "paper", value: "#f4f0e6" },
      ],
    },
  },
  tags: ["autodocs"],
  argTypes: {
    commandColor: {
      control: "color",
      description: "Header and unit-symbol color",
    },
    bodyColor: {
      control: "color",
      description: "Main card background color",
    },
    footerColor: {
      control: "color",
      description: "Scenario footer color",
    },
  },
} satisfies Meta<typeof CommandCard>;

export default meta;
type Story = StoryObj<typeof meta>;

const agaFooter = "#315d46";

const beauregardUnits: CommandCardProps["units"] = [
  { name: "Cocke", type: "Inf" },
  { name: "Hunton", type: "Inf" },
  { name: "Early", type: "Inf" },
  { name: "Ewell", type: "Inf" },
  { name: "Evans", type: "Inf" },
  { name: "Kershaw", type: "Inf" },
];

const jacksonUnits: CommandCardProps["units"] = [
  { name: "Elzey", type: "Inf" },
  { name: "Jackson", type: "Inf" },
  { name: "Bartow", type: "Inf" },
  { name: "Bee", type: "Inf" },
];

const porterUnits: CommandCardProps["units"] = [
  { name: "Burnside-B", type: "Inf" },
  { name: "Lyons", type: "Inf" },
];

export const BeauregardSixUnits: Story = {
  args: {
    title: "P Beauregard",
    side: "confederate",
    commandColor: "#df8d3d",
    bodyColor: "#c8c8c4",
    footerColor: agaFooter,
    gameName: "All Green Alike",
    scenarioNumber: 5,
    units: beauregardUnits,
  },
};

export const JohnstonFourUnits: Story = {
  args: {
    title: "S Johnston",
    side: "confederate",
    commandColor: "#75b94d",
    bodyColor: "#c8c8c4",
    footerColor: agaFooter,
    gameName: "All Green Alike",
    scenarioNumber: 5,
    units: jacksonUnits,
  },
};

export const PorterTwoUnits: Story = {
  args: {
    title: "2-V Porter",
    side: "union",
    commandColor: "#77a9d3",
    bodyColor: "#b9daea",
    footerColor: agaFooter,
    gameName: "All Green Alike",
    scenarioNumber: 5,
    units: porterUnits,
  },
};

export const Continuation: Story = {
  args: {
    ...BeauregardSixUnits.args,
    units: [
      { name: "Bonham", type: "Inf" },
      { name: "Longstreet", type: "Inf" },
      { name: "Jones", type: "Inf" },
    ],
    continuation: true,
  },
};

export const ScenarioFiveSheet: Story = {
  args: BeauregardSixUnits.args,
  render: () => (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(2, 3.5in)",
        gap: "0.18in",
        padding: "0.25in",
        background: "#d8d2c2",
      }}
    >
      <CommandCard {...BeauregardSixUnits.args} />
      <CommandCard {...Continuation.args} />
      <CommandCard {...JohnstonFourUnits.args} />
      <CommandCard {...PorterTwoUnits.args} />
    </div>
  ),
};
