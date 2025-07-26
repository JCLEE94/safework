import React from 'react';
import { Button as AntButton, ButtonProps as AntButtonProps } from 'antd';
import styled from 'styled-components';

export interface ButtonProps extends AntButtonProps {
  fullWidth?: boolean;
}

const StyledButton = styled(AntButton)<{ $fullWidth?: boolean }>`
  ${props => props.$fullWidth && 'width: 100%;'}
  
  &.secondary {
    background-color: #f0f0f0;
    border-color: #d9d9d9;
    color: rgba(0, 0, 0, 0.85);
    
    &:hover {
      background-color: #e6e6e6;
      border-color: #d9d9d9;
    }
  }
`;

export const Button: React.FC<ButtonProps> = ({ 
  fullWidth,
  ...props 
}) => {
  return (
    <StyledButton
      {...props}
      $fullWidth={fullWidth}
    />
  );
};