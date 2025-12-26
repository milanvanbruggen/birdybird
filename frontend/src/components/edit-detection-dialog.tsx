import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Trash2, Save } from "lucide-react";
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

interface Detection {
    id: number;
    species: string;
    confidence: number;
    image_path: string;
    timestamp: string;
    interesting_fact: string;
}

interface EditDetectionDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    detection: Detection | null;
    onUpdate: () => void;
}

export function EditDetectionDialog({ open, onOpenChange, detection, onUpdate }: EditDetectionDialogProps) {
    const [species, setSpecies] = useState("");
    const [confidence, setConfidence] = useState(0);
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

    useEffect(() => {
        if (detection) {
            setSpecies(detection.species);
            setConfidence(detection.confidence);
            setShowDeleteConfirm(false);
        }
    }, [detection]);

    const handleSave = () => {
        if (!detection) return;
        fetch(`/api/detections/${detection.id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                species,
                confidence: confidence,
                interesting_fact: "" // We aren't editing this anymore, but the backend expects it.
            })
        })
            .then(res => {
                if (res.ok) {
                    onUpdate();
                    onOpenChange(false);
                }
            });
    };

    const handleDeleteClick = () => {
        setShowDeleteConfirm(true);
    };

    const confirmDelete = () => {
        if (!detection) return;
        fetch(`/api/detections/${detection.id}`, { method: 'DELETE' })
            .then(res => {
                if (res.ok) {
                    onUpdate();
                    onOpenChange(false);
                    setShowDeleteConfirm(false);
                }
            });
    };

    if (!detection) return null;

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle>Edit Detection</DialogTitle>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                    <div className="w-full aspect-video rounded-lg overflow-hidden bg-black">
                        <img src={detection.image_path} alt={detection.species} className="w-full h-full object-contain" />
                    </div>

                    <div className="grid grid-cols-4 items-center gap-4">
                        <Label htmlFor="species" className="text-right">
                            Species
                        </Label>
                        <Input
                            id="species"
                            value={species}
                            onChange={(e) => setSpecies(e.target.value)}
                            className="col-span-3"
                        />
                    </div>
                    <div className="grid grid-cols-4 items-center gap-4">
                        <Label htmlFor="confidence" className="text-right">
                            Score (%)
                        </Label>
                        <Input
                            id="confidence"
                            type="number"
                            min="0"
                            max="100"
                            value={Math.round(confidence * 100)}
                            onChange={(e) => setConfidence(Number(e.target.value) / 100)}
                            className="col-span-3"
                        />
                    </div>
                    <div className="text-xs text-muted-foreground text-center">
                        Detected on {new Date(detection.timestamp).toLocaleString()}
                    </div>
                </div>
                <DialogFooter className="flex justify-between sm:justify-between w-full">
                    <Button variant="destructive" onClick={handleDeleteClick} type="button">
                        <Trash2 className="w-4 h-4 mr-2" /> Delete
                    </Button>
                    <Button onClick={handleSave} type="submit">
                        <Save className="w-4 h-4 mr-2" /> Save
                    </Button>
                </DialogFooter>

                <AlertDialog open={showDeleteConfirm} onOpenChange={setShowDeleteConfirm}>
                    <AlertDialogContent>
                        <AlertDialogHeader>
                            <AlertDialogTitle>Delete this detection?</AlertDialogTitle>
                            <AlertDialogDescription>
                                This will permanently remove this bird record and its image.
                            </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                            <AlertDialogCancel>Cancel</AlertDialogCancel>
                            <AlertDialogAction onClick={confirmDelete} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
                                Delete
                            </AlertDialogAction>
                        </AlertDialogFooter>
                    </AlertDialogContent>
                </AlertDialog>
            </DialogContent>
        </Dialog>
    );
}
