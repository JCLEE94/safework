import React from 'react';
import { Tooltip } from 'antd';
import styled from 'styled-components';

interface TextEllipsisProps {
  children: React.ReactNode;
  width?: number | string;
  lines?: number;
  showTooltip?: boolean;
  className?: string;
}

const EllipsisContainer = styled.div<{ width?: number | string; lines?: number }>`
  width: ${props => typeof props.width === 'number' ? `${props.width}px` : props.width || '100%'};
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: ${props => props.lines && props.lines > 1 ? 'normal' : 'nowrap'};
  ${props => props.lines && props.lines > 1 && `
    display: -webkit-box;
    -webkit-line-clamp: ${props.lines};
    -webkit-box-orient: vertical;
  `}
`;

export const TextEllipsis: React.FC<TextEllipsisProps> = ({
  children,
  width,
  lines = 1,
  showTooltip = true,
  className
}) => {
  const text = typeof children === 'string' ? children : '';
  
  const content = (
    <EllipsisContainer width={width} lines={lines} className={className}>
      {children}
    </EllipsisContainer>
  );

  if (showTooltip && text) {
    return (
      <Tooltip title={text} placement="topLeft">
        {content}
      </Tooltip>
    );
  }

  return content;
};

export default TextEllipsis;