'use client';

import { useEffect } from "react";
import { motion } from 'framer-motion';
import { CreditCard, TrendingUp, Shield, DollarSign, PieChart, Users } from 'lucide-react';
import AnimatedLogo from '@/components/ui/AnimatedLogo';
import ThemeToggle from '@/components/ui/ThemeToggle';
import { LoginForm } from '@/components/LoginForm';

export default function Home() {
  useEffect(() => {
    // Initialize session on component mount
