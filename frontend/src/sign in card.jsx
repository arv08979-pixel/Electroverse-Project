import React, { useState, useContext } from 'react';
import TextInput from './TextInput';
import Button from './Button';
import AuthContext from './AuthContext.jsx';

const SignInCard = () => {
  const [formData, setFormData] = useState({ email: '', password: '' });

  const handleChange = (field, value) => {
    setFormData({ ...formData, [field]: value });
  };

  const auth = useContext(AuthContext);

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      const result = await auth.login(formData);
      if (!result.success) {
        alert(result.message || 'Login failed');
        return;
      }
    } catch (err) {
      alert('Network error');
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <div style={styles.brand}>
          <div style={styles.logo}>EV</div>
          <div style={styles.brandText}>Electroverse</div>
        </div>

        <h2 style={styles.title}>Welcome back</h2>
        <p style={styles.subtitle}>Secure access to encrypted recordings</p>

        <form onSubmit={handleSubmit} style={styles.form}>
          <TextInput label="Email Address" type="email" placeholder="name@company.com" value={formData.email} onChange={(val) => handleChange('email', val)} />
          <TextInput label="Password" type="password" placeholder="Enter your password" value={formData.password} onChange={(val) => handleChange('password', val)} />

          <div style={{ marginTop: 12 }}>
            <Button label="Sign In" type="submit" style={{ width: '100%' }} />
          </div>
        </form>
      </div>
    </div>
  );
};

const styles = {
  container: { display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '70vh', padding: 20, background: 'linear-gradient(180deg,#0f172a 0%, #071033 100%)' },
  card: { backgroundColor: '#0f172a', color: '#e6eef8', padding: 28, borderRadius: 12, boxShadow: '0 10px 30px rgba(2,6,23,0.6)', width: '100%', maxWidth: 420, fontFamily: "Inter, 'Segoe UI', Roboto, Arial, sans-serif" },
  brand: { display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14 },
  logo: { width: 40, height: 40, borderRadius: 8, background: 'linear-gradient(90deg,#2563EB,#7C3AED)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: '700' },
  brandText: { fontWeight: 700, fontSize: 18, color: '#fff' },
  title: { margin: '6px 0 4px', fontSize: 20, color: '#f8fafc' },
  subtitle: { margin: 0, color: '#9aa7bf', fontSize: 13 },
  form: { marginTop: 14 },
};

export default SignInCard;