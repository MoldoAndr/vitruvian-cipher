import React from 'react';
import { AppProvider } from './contexts/AppContext';
import MainLayout from './components/MainLayout';
import FluidBackground from './components/FluidBackground';

function App() {
  return (
    <AppProvider>
      <FluidBackground />
      <MainLayout />
    </AppProvider>
  );
}

export default App;
