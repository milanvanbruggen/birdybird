import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Camera, RefreshCw } from "lucide-react";
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"


export function StreamPanel() {
    const [cameras, setCameras] = useState<{ id: number; name: string }[]>([]);
    const [selectedCamera, setSelectedCamera] = useState<string>("");
    const [debugMode, setDebugMode] = useState(false);
    const [streamUrl, setStreamUrl] = useState("/video_feed");
    const [status, setStatus] = useState({ processing: false, cooldown: 0 });

    useEffect(() => {
        // Load cameras
        fetch('/api/cameras')
            .then(res => res.json())
            .then(data => {
                setCameras(data);
                if (data.length > 0) setSelectedCamera(String(data[0].id));
            });

        // Poll status
        const interval = setInterval(() => {
            fetch('/api/status')
                .then(res => res.json())
                .then(data => setStatus(data));
        }, 1000);

        return () => clearInterval(interval);
    }, []);

    const handleCameraChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        const camId = e.target.value;
        setSelectedCamera(camId);
        fetch(`/api/cameras/${camId}`, { method: 'POST' })
            .then(() => {
                // Force refresh stream
                setStreamUrl("");
                setTimeout(() => setStreamUrl(`/video_feed?t=${Date.now()}`), 200);
            });
    };

    const toggleDebug = (checked: boolean) => {
        setDebugMode(checked);
        fetch(`/api/debug/${checked}`, { method: 'POST' });
    };

    return (
        <Card className="h-full flex flex-col border-border/50 bg-card/50 backdrop-blur">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-xl font-bold flex items-center gap-2">
                    <Camera className="w-5 h-5 text-accent" />
                    Live Stream
                </CardTitle>
                <div className="flex items-center gap-4">
                    <div className="flex items-center space-x-2">
                        <Switch id="debug-mode" checked={debugMode} onCheckedChange={toggleDebug} />
                        <Label htmlFor="debug-mode">Debug Overlay</Label>
                    </div>
                    <select
                        className="bg-background border border-input rounded px-2 py-1 text-sm"
                        value={selectedCamera}
                        onChange={handleCameraChange}
                    >
                        {cameras.map(cam => (
                            <option key={cam.id} value={cam.id}>{cam.name}</option>
                        ))}
                    </select>
                    {status.processing && (
                        <span className="text-xs font-bold text-accent animate-pulse">ANALYZING...</span>
                    )}
                    {!status.processing && status.cooldown > 0 && (
                        <span className="text-xs text-muted-foreground">Cooling down ({Math.ceil(status.cooldown)}s)</span>
                    )}
                </div>
            </CardHeader>
            <CardContent className="flex-1 p-0 relative min-h-[400px] overflow-hidden rounded-b-lg">
                {streamUrl ? (
                    <img
                        src={streamUrl}
                        alt="Live Feed"
                        className="w-full h-full object-cover"
                    />
                ) : (
                    <div className="w-full h-full flex items-center justify-center bg-black/90 text-muted-foreground">
                        <RefreshCw className="w-8 h-8 animate-spin" />
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
