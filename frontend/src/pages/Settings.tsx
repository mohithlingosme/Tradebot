import { useState } from 'react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Switch } from '../components/ui/switch';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../hooks/use-toast';

const Settings = () => {
  const { theme, toggleTheme } = useTheme();
  const { user } = useAuth();
  const { toast } = useToast();

  const [profile, setProfile] = useState({
    name: user?.name || '',
    email: user?.email || '',
  });

  const [apiKeys, setApiKeys] = useState({
    alpacaKey: '',
    alpacaSecret: '',
  });

  const [notifications, setNotifications] = useState({
    emailAlerts: true,
    pushNotifications: false,
    riskAlerts: true,
    tradeConfirmations: true,
  });

  const handleProfileUpdate = () => {
    toast({
      title: 'Success',
      description: 'Profile updated successfully',
    });
  };

  const handleApiKeyUpdate = () => {
    toast({
      title: 'Success',
      description: 'API keys updated successfully',
    });
  };

  const handleNotificationUpdate = () => {
    toast({
      title: 'Success',
      description: 'Notification preferences updated',
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Settings</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Profile</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Full Name</label>
              <Input
                value={profile.name}
                onChange={(e) => setProfile({ ...profile, name: e.target.value })}
                placeholder="Enter your full name"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Email</label>
              <Input
                type="email"
                value={profile.email}
                onChange={(e) => setProfile({ ...profile, email: e.target.value })}
                placeholder="Enter your email"
              />
            </div>
            <Button onClick={handleProfileUpdate}>Update Profile</Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Theme</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Dark Mode</p>
                <p className="text-sm text-muted-foreground">Toggle between light and dark themes</p>
              </div>
              <Switch checked={theme === 'dark'} onCheckedChange={toggleTheme} />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">API Keys</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Alpaca API Key</label>
              <Input
                type="password"
                value={apiKeys.alpacaKey}
                onChange={(e) => setApiKeys({ ...apiKeys, alpacaKey: e.target.value })}
                placeholder="Enter your Alpaca API key"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Alpaca API Secret</label>
              <Input
                type="password"
                value={apiKeys.alpacaSecret}
                onChange={(e) => setApiKeys({ ...apiKeys, alpacaSecret: e.target.value })}
                placeholder="Enter your Alpaca API secret"
              />
            </div>
            <Button onClick={handleApiKeyUpdate}>Update API Keys</Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Notifications</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Email Alerts</p>
                <p className="text-sm text-muted-foreground">Receive alerts via email</p>
              </div>
              <Switch
                checked={notifications.emailAlerts}
                onCheckedChange={(checked) => setNotifications({ ...notifications, emailAlerts: checked })}
              />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Push Notifications</p>
                <p className="text-sm text-muted-foreground">Receive push notifications</p>
              </div>
              <Switch
                checked={notifications.pushNotifications}
                onCheckedChange={(checked: boolean) => setNotifications({ ...notifications, pushNotifications: checked })}
              />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Risk Alerts</p>
                <p className="text-sm text-muted-foreground">Get notified of risk events</p>
              </div>
              <Switch
                checked={notifications.riskAlerts}
                onCheckedChange={(checked: boolean) => setNotifications({ ...notifications, riskAlerts: checked })}
              />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Trade Confirmations</p>
                <p className="text-sm text-muted-foreground">Confirm before executing trades</p>
              </div>
              <Switch
                checked={notifications.tradeConfirmations}
                onCheckedChange={(checked: boolean) => setNotifications({ ...notifications, tradeConfirmations: checked })}
              />
            </div>
            <Button onClick={handleNotificationUpdate}>Update Preferences</Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Settings;
