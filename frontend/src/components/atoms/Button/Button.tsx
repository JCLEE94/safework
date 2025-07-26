import React from 'react';
import { Button as AntButton, ButtonProps as AntButtonProps } from 'antd';
import styled from 'styled-components';
import { designTokens } from '../../../styles/theme';

type CustomVariant = 'primary' | 'secondary' | 'outline' | 'text' | 'danger';

export interface ButtonProps extends Omit<AntButtonProps, 'variant'> {
  variant?: CustomVariant;
  fullWidth?: boolean;
}

const StyledButton = styled(AntButton)<{ $fullWidth?: boolean }>`
  font-weight: ${designTokens.typography.fontWeight.medium};
  transition: all ${designTokens.transitions.fast} ease;
  width: ${props => props.$fullWidth ? '100%' : 'auto'};
  
  &:hover {
    transform: translateY(-1px);
    box-shadow: ${designTokens.shadows.md};
  }
  
  &:active {
    transform: translateY(0);
  }
  
  &.ant-btn-primary {
    background: ${designTokens.colors.primary[500]};
    border-color: ${designTokens.colors.primary[500]};
    
    &:hover {
      background: ${designTokens.colors.primary[600]};
      border-color: ${designTokens.colors.primary[600]};
    }
  }
  
  &.ant-btn-default {
    border-color: ${designTokens.colors.neutral[300]};
    color: ${designTokens.colors.neutral[700]};
    
    &:hover {
      border-color: ${designTokens.colors.primary[500]};
      color: ${designTokens.colors.primary[500]};
    }
  }
  
  &.ant-btn-dangerous {
    background: ${designTokens.colors.error[500]};
    border-color: ${designTokens.colors.error[500]};
    
    &:hover {
      background: ${designTokens.colors.error[600]};
      border-color: ${designTokens.colors.error[600]};
    }
  }
  
  &.ant-btn-text {
    border: none;
    box-shadow: none;
    
    &:hover {
      background: ${designTokens.colors.neutral[50]};
      transform: none;
      box-shadow: none;
    }
  }
`;

export const Button: React.FC<ButtonProps> = ({ 
  variant = 'primary',
  fullWidth = false,
  danger,
  ...props 
}) => {
  const getButtonType = () => {
    switch (variant) {
      case 'primary':
        return 'primary';
      case 'secondary':
      case 'outline':
        return 'default';
      case 'text':
        return 'text';
      case 'danger':
        return 'primary';
      default:
        return 'primary';
    }
  };
  
  return (
    <StyledButton
      type={getButtonType()}
      danger={variant === 'danger'}
      $fullWidth={fullWidth}
      {...props}
    />
  );
};