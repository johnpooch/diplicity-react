import { Meta, StoryObj } from "@storybook/react";
import { TestMap } from "./test-map";

export default {
    title: "Components/Maps/TestMap",
    component: TestMap,
} as Meta;

type Story = StoryObj<typeof TestMap>;

export const Default: Story = {};
