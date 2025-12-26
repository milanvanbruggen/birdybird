import { useState, useEffect } from 'react';
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Trash2 } from "lucide-react";
import { EditDetectionDialog } from './edit-detection-dialog';

interface Detection {
    id: number;
    species: string;
    confidence: number;
    image_path: string;
    timestamp: string;
    interesting_fact: string;
}

import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from "@/components/ui/alert-dialog";

export function DetectionList() {
    const [detections, setDetections] = useState<Detection[]>([]);
    const [selectedDetection, setSelectedDetection] = useState<Detection | null>(null);
    const [isDialogOpen, setIsDialogOpen] = useState(false);
    const [showClearConfirm, setShowClearConfirm] = useState(false);

    const fetchDetections = () => {
        fetch('/api/detections')
            .then(res => res.json())
            .then(data => setDetections(data));
    };

    useEffect(() => {
        fetchDetections();
        const interval = setInterval(fetchDetections, 3000);
        return () => clearInterval(interval);
    }, []);

    const handleClearAll = () => {
        setShowClearConfirm(true);
    };

    const confirmClearAll = () => {
        fetch('/api/detections', { method: 'DELETE' })
            .then(() => {
                fetchDetections();
                setShowClearConfirm(false);
            });
    };

    const handleCardClick = (detection: Detection) => {
        setSelectedDetection(detection);
        setIsDialogOpen(true);
    };

    return (
        <Card className="h-full flex flex-col border-border/50 bg-card/50 backdrop-blur">
            <div className="p-4 border-b border-border flex justify-between items-center">
                <h2 className="font-bold text-lg">Recent Detections</h2>
                <Button variant="ghost" size="icon" onClick={handleClearAll} title="Clear All">
                    <Trash2 className="w-4 h-4 text-muted-foreground hover:text-destructive" />
                </Button>
            </div>

            <AlertDialog open={showClearConfirm} onOpenChange={setShowClearConfirm}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
                        <AlertDialogDescription>
                            This action cannot be undone. This will permanently delete all detection logs and images.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction onClick={confirmClearAll} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
                            Delete All
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>

            <ScrollArea className="flex-1 p-4">
                <div className="flex flex-col gap-3">
                    {detections.length === 0 ? (
                        <div className="text-center text-muted-foreground py-10">
                            No birds detected yet.
                        </div>
                    ) : (
                        detections.map(d => (
                            <div
                                key={d.id}
                                className="flex gap-3 p-3 rounded-lg border border-border/40 bg-card/40 hover:bg-accent/10 hover:border-accent/50 transition-all cursor-pointer"
                                onClick={() => handleCardClick(d)}
                            >
                                <img
                                    src={d.image_path}
                                    alt={d.species}
                                    className="w-20 h-20 rounded object-cover bg-black"
                                />
                                <div className="flex-1 flex flex-col justify-center">
                                    <h3 className="font-bold text-primary">{d.species}</h3>
                                    <div className="text-xs text-muted-foreground space-x-2">
                                        <span>{new Date(d.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                                        <span>&bull;</span>
                                        <span>{Math.round(d.confidence * 100)}% Match</span>
                                    </div>
                                    <p className="text-xs text-accent line-clamp-1 mt-1">
                                        {d.confidence < 0.4 ? "Low confidence match" : "Visual match confirmed"}
                                    </p>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </ScrollArea>

            <EditDetectionDialog
                open={isDialogOpen}
                onOpenChange={setIsDialogOpen}
                detection={selectedDetection}
                onUpdate={fetchDetections}
            />
        </Card >
    );
}
