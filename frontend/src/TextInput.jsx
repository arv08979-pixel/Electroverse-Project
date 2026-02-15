import React from 'react';

const TextInput = ({ label, type = 'text', placeholder = '', value, onChange }) => {
  return (
    <div style={{ marginBottom: 12 }}>
      {label ? <label style={{ display: 'block', marginBottom: 6 }}>{label}</label> : null}
      <input
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        style={{ width: '100%', padding: '8px 10px', borderRadius: 6, border: '1px solid #ddd' }}
      />
    </div>
  );
};

export default TextInput;
