import { File } from 'expo-file-system';
import * as Location from 'expo-location';
import { ImageManipulator, SaveFormat } from 'expo-image-manipulator';
import { Logger } from '@/src/services/LoggerService';
import { NotificationService } from '@/src/services/NotificationService';

export const MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024;
export const IMAGE_TOO_LARGE_CODE = 'IMAGE_TOO_LARGE_MAX_5MB';

export const validateIsJpg = (uri: string) => {
  const extension = uri.split('.').pop()?.toLowerCase();
  return extension === 'jpg' || extension === 'jpeg';
};

export const getImageSize = (uri: string) => {
  const file = new File(uri);
  if (!file.exists) return null;
  return file.info().size ?? 0;
};

export const getLocationData = async (translations: {
  unknownLocation: string;
  unknownCity: string;
  unknownCountry: string;
}) => {
  let locationStr = translations.unknownLocation;
  let latitude: number | undefined;
  let longitude: number | undefined;

  try {
    const { status } = await Location.requestForegroundPermissionsAsync();
    if (status !== 'granted') {
      Logger.info("Permiso de ubicación denegado; se usará 'Ubicación desconocida'");
      return { locationStr, latitude, longitude };
    }

    const loc = await Location.getCurrentPositionAsync({
      accuracy: Location.Accuracy.Balanced,
    });
    latitude = loc.coords.latitude;
    longitude = loc.coords.longitude;

    try {
      const geocode = await Location.reverseGeocodeAsync({
        latitude: loc.coords.latitude,
        longitude: loc.coords.longitude,
      });

      if (geocode && geocode.length > 0) {
        const address = geocode[0];
        const city = address.city || address.subregion || address.region || translations.unknownCity;
        const country = address.country || translations.unknownCountry;
        locationStr = `${city}, ${country}`;
      } else {
        locationStr = `${loc.coords.latitude.toFixed(4)}, ${loc.coords.longitude.toFixed(4)}`;
      }
    } catch (geoError) {
      Logger.warn('Error en reverse geocoding', geoError);
      locationStr = `${loc.coords.latitude.toFixed(4)}, ${loc.coords.longitude.toFixed(4)}`;
    }
  } catch (error) {
    Logger.warn('Error obteniendo ubicación', error);
  }

  return { locationStr, latitude, longitude };
};

export const getFCMToken = async () => {
  try {
    return await NotificationService.getPushTokenAsync();
  } catch (error) {
    Logger.warn('Error obtaining FCM token', error);
    return undefined;
  }
};

export const optimizeImage = async (uri: string) => {
  try {
    const context = ImageManipulator.manipulate(uri);
    const image = await context.renderAsync();
    const result = await image.saveAsync({ compress: 0.9, format: SaveFormat.JPEG });
    return result.uri;
  } catch (error) {
    Logger.warn('Error manipulando imagen (EXIF)', error);
    return uri;
  }
};
