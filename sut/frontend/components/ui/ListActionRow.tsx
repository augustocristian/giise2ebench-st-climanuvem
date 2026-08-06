import React from 'react';
import { StyleProp, Text, TextStyle, TouchableOpacity, View, ViewStyle } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface ListActionRowProps {
  readonly icon: keyof typeof Ionicons.glyphMap;
  readonly title: string;
  readonly description: string;
  readonly onPress: () => void;
  readonly iconColor: string;
  readonly iconBackgroundColor: string;
  readonly chevronColor: string;
  readonly size?: number;
  readonly cardStyle: StyleProp<ViewStyle>;
  readonly iconContainerStyle: StyleProp<ViewStyle>;
  readonly textContainerStyle: StyleProp<ViewStyle>;
  readonly titleStyle: StyleProp<TextStyle>;
  readonly descriptionStyle: StyleProp<TextStyle>;
}

export const ListActionRow = ({
  icon,
  title,
  description,
  onPress,
  iconColor,
  iconBackgroundColor,
  chevronColor,
  size = 28,
  cardStyle,
  iconContainerStyle,
  textContainerStyle,
  titleStyle,
  descriptionStyle,
}: ListActionRowProps) => (
  <TouchableOpacity style={cardStyle} onPress={onPress} accessibilityRole="button">
    <View style={[iconContainerStyle, { backgroundColor: iconBackgroundColor }]}>
      <Ionicons name={icon} size={size} color={iconColor} />
    </View>
    <View style={textContainerStyle}>
      <Text style={titleStyle}>{title}</Text>
      <Text style={descriptionStyle}>{description}</Text>
    </View>
    <Ionicons name="chevron-forward" size={20} color={chevronColor} />
  </TouchableOpacity>
);
