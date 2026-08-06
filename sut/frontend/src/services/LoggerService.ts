type LogLevel = 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR';

const LEVEL_PRIORITY: Record<LogLevel, number> = {
  DEBUG: 10,
  INFO: 20,
  WARNING: 30,
  ERROR: 40,
};

const MIN_LEVEL: LogLevel = __DEV__ ? 'DEBUG' : 'INFO';

const shouldLog = (level: LogLevel): boolean => {
  return LEVEL_PRIORITY[level] >= LEVEL_PRIORITY[MIN_LEVEL];
};

const prefix = (level: LogLevel, message: string): string => {
  return `[${level}] ${message}`;
};

const log = (level: LogLevel, message: string, meta?: unknown) => {
  if (!shouldLog(level)) return;

  if (meta !== undefined) {
    if (level === 'ERROR') {
      console.error(prefix(level, message), meta);
      return;
    }
    if (level === 'WARNING') {
      console.warn(prefix(level, message), meta);
      return;
    }
    if (level === 'INFO') {
      console.info(prefix(level, message), meta);
      return;
    }
    console.debug(prefix(level, message), meta);
    return;
  }

  if (level === 'ERROR') {
    console.error(prefix(level, message));
    return;
  }
  if (level === 'WARNING') {
    console.warn(prefix(level, message));
    return;
  }
  if (level === 'INFO') {
    console.info(prefix(level, message));
    return;
  }
  console.debug(prefix(level, message));
};

export const Logger = {
  debug: (message: string, meta?: unknown) => log('DEBUG', message, meta),
  info: (message: string, meta?: unknown) => log('INFO', message, meta),
  warn: (message: string, meta?: unknown) => log('WARNING', message, meta),
  error: (message: string, meta?: unknown) => log('ERROR', message, meta),
};
