import * as Notifications from 'expo-notifications';

export const useNotificationResponse = () => {
  return Notifications.useLastNotificationResponse();
};
