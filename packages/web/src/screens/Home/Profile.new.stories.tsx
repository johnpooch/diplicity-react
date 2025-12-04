import type { Meta, StoryObj } from "@storybook/react";
import { action } from "@storybook/addon-actions";
import { Profile } from "./Profile.new";

const meta = {
  title: "Screens/Profile",
  component: Profile,
  parameters: {
    layout: "fullscreen",
  },
} satisfies Meta<typeof Profile>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    isLoading: false,
    userProfile: {
      name: "John Smith",
      picture: null,
    },
    onUpdateName: action("update-name"),
    isSubmitting: false,
    pushNotificationsEnabled: false,
    pushNotificationsPermissionDenied: false,
    pushNotificationsError: undefined,
    onTogglePushNotifications: action("toggle-push-notifications"),
    onLogout: action("logout"),
  },
};

export const WithAvatar: Story = {
  args: {
    isLoading: false,
    userProfile: {
      name: "Jane Doe",
      picture: "https://i.pravatar.cc/150?img=5",
    },
    onUpdateName: action("update-name"),
    isSubmitting: false,
    pushNotificationsEnabled: true,
    pushNotificationsPermissionDenied: false,
    pushNotificationsError: undefined,
    onTogglePushNotifications: action("toggle-push-notifications"),
    onLogout: action("logout"),
  },
};

export const EditingName: Story = {
  args: {
    isLoading: false,
    userProfile: {
      name: "John Smith",
      picture: null,
    },
    onUpdateName: action("update-name"),
    isSubmitting: false,
    pushNotificationsEnabled: false,
    pushNotificationsPermissionDenied: false,
    pushNotificationsError: undefined,
    onTogglePushNotifications: action("toggle-push-notifications"),
    onLogout: action("logout"),
  },
};

export const SavingName: Story = {
  args: {
    isLoading: false,
    userProfile: {
      name: "John Smith",
      picture: null,
    },
    onUpdateName: action("update-name"),
    isSubmitting: true,
    pushNotificationsEnabled: false,
    pushNotificationsPermissionDenied: false,
    pushNotificationsError: undefined,
    onTogglePushNotifications: action("toggle-push-notifications"),
    onLogout: action("logout"),
  },
};

export const SaveNameError: Story = {
  args: {
    isLoading: false,
    userProfile: {
      name: "John Smith",
      picture: null,
    },
    onUpdateName: async () => {
      await action("update-name")();
      throw new Error("Failed to update name");
    },
    isSubmitting: false,
    pushNotificationsEnabled: false,
    pushNotificationsPermissionDenied: false,
    pushNotificationsError: undefined,
    onTogglePushNotifications: action("toggle-push-notifications"),
    onLogout: action("logout"),
  },
};

export const Loading: Story = {
  args: {
    isLoading: true,
    userProfile: undefined,
    onUpdateName: action("update-name"),
    isSubmitting: false,
    pushNotificationsEnabled: false,
    pushNotificationsPermissionDenied: false,
    pushNotificationsError: undefined,
    onTogglePushNotifications: action("toggle-push-notifications"),
    onLogout: action("logout"),
  },
};

export const NotificationsEnabled: Story = {
  args: {
    isLoading: false,
    userProfile: {
      name: "John Smith",
      picture: null,
    },
    onUpdateName: action("update-name"),
    isSubmitting: false,
    pushNotificationsEnabled: true,
    pushNotificationsPermissionDenied: false,
    pushNotificationsError: undefined,
    onTogglePushNotifications: action("toggle-push-notifications"),
    onLogout: action("logout"),
  },
};

export const NotificationsPermissionDenied: Story = {
  args: {
    isLoading: false,
    userProfile: {
      name: "John Smith",
      picture: null,
    },
    onUpdateName: action("update-name"),
    isSubmitting: false,
    pushNotificationsEnabled: false,
    pushNotificationsPermissionDenied: true,
    pushNotificationsError: undefined,
    onTogglePushNotifications: action("toggle-push-notifications"),
    onLogout: action("logout"),
  },
};

export const NotificationsError: Story = {
  args: {
    isLoading: false,
    userProfile: {
      name: "John Smith",
      picture: null,
    },
    onUpdateName: action("update-name"),
    isSubmitting: false,
    pushNotificationsEnabled: false,
    pushNotificationsPermissionDenied: false,
    pushNotificationsError: "Failed to register service worker",
    onTogglePushNotifications: action("toggle-push-notifications"),
    onLogout: action("logout"),
  },
};
