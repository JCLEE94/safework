import React from 'react';
import { Card as AntCard, CardProps } from 'antd';
import styled from 'styled-components';

const StyledCard = styled(AntCard)`
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  transition: all 0.3s ease;
  
  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }
`;

export const Card: React.FC<CardProps> = (props) => {
  return <StyledCard {...props} />;
};