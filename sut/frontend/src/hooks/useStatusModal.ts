import { useState } from 'react';
import type { ModalType } from '@/components/ui/StatusModal';

export type StatusModalConfig = {
  type: ModalType;
  title: string;
  message: string;
  onClose?: () => void;
  onCancel?: () => void;
};

const DEFAULT_MODAL_CONFIG: StatusModalConfig = {
  type: 'info',
  title: '',
  message: '',
};

export const useStatusModal = () => {
  const [modalVisible, setModalVisible] = useState(false);
  const [modalConfig, setModalConfig] = useState<StatusModalConfig>(DEFAULT_MODAL_CONFIG);

  const showModal = (
    type: ModalType,
    title: string,
    message: string,
    onClose?: () => void,
    onCancel?: () => void,
  ) => {
    setModalConfig({ type, title, message, onClose, onCancel });
    setModalVisible(true);
  };

  const hideModal = () => {
    setModalVisible(false);
  };

  return {
    modalVisible,
    modalConfig,
    showModal,
    hideModal,
  };
};
