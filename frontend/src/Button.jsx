import React from 'react';

const Button = ({ label = 'Submit', onClick, type = 'button', style = {} }) => {
  return (
    <button
      type={type}
      onClick={onClick}
      style={{
        padding: '10px 14px',
        backgroundColor: '#2563EB',
        color: '#fff',
        border: 'none',
        borderRadius: 8,
        cursor: 'pointer',
        ...style,
      }}
    >
      {label}
    </button>
  );
};

export default Button;
