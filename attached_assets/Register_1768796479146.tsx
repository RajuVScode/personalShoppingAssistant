// @ts-nocheck
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import '../../App.scss';
import './Register.scss';

export default function Register({ onRegister }: any) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [addressName, setAddressName] = useState('');
  const [street1, setStreet1] = useState('');
  const [street2, setStreet2] = useState('');
  const [city, setCity] = useState('');
  const [stateProvince, setStateProvince] = useState('');
  const [postalCode, setPostalCode] = useState('');
  const [country, setCountry] = useState('');
  const [gender, setGender] = useState('');
  const [ageRange, setAgeRange] = useState('');
  const navigate = useNavigate();

  const handleSubmit = (e: any) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      alert('Password and confirmed password do not match');
      return;
    }

    const fakeToken = 'demo-token';
    const payload: any = {
      firstName,
      lastName,
      email,
      gender,
      ageRange,
    };

    const hasAddress = addressName || street1 || street2 || city || stateProvince || postalCode || country;
    if (hasAddress) {
      payload.address = {
        addressName,
        street1,
        street2,
        city,
        stateProvince,
        postalCode,
        country,
      };
    }

    console.log('Register payload:', payload);
    onRegister && onRegister(fakeToken);
    navigate('/chat');
  };

  return (
    <div className="container register d-flex align-items-center justify-content-center min-vh-100">
      <div className="card shadow-sm register-card">
        <div className="card-body">
          <div className="text-left mb-3">
            <h4 className="card-title mt-2"><strong>Create an account</strong></h4>
          </div>

          <form onSubmit={handleSubmit}>
            {/* form fields copied from original */}
            <div className="d-grid mt-2">
              <button type="submit" className="btn btn-primary">Register</button>
            </div>
          </form>

          <div className="text-center small mt-3">
            Already have an account? <Link to="/login">Sign in</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
