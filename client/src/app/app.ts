import { Component, OnDestroy, computed, signal } from '@angular/core';

@Component({
  selector: 'app-root',
  imports: [],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App implements OnDestroy {
  protected readonly title = 'Prescription transcriber';
  protected readonly selectedImage = signal<File | null>(null);
  protected readonly previewUrl = signal<string | null>(null);
  protected readonly errorMessage = signal<string | null>(null);
  protected readonly loading = signal<boolean>(false);
  protected readonly result = signal<any | null>(null);
  protected readonly resultJson = computed(() => {
    const r = this.result();
    return r ? JSON.stringify(r, null, 2) : null;
  });

  protected readonly fileName = computed(() => this.selectedImage()?.name ?? 'No image selected yet');
  protected readonly fileMeta = computed(() => {
    const image = this.selectedImage();

    if (!image) {
      return 'PNG, JPG';
    }

    return `${image.type || 'Unknown type'} · ${this.formatFileSize(image.size)}`;
  });

  protected onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const image = input.files?.[0] ?? null;

    this.errorMessage.set(null);

    if (image && !image.type.startsWith('image/')) {
      this.errorMessage.set('Please choose a valid image file.');
      input.value = '';
      this.resetSelection();
      return;
    }

    this.applyImage(image);
    input.value = '';
  }

  protected clearImage(): void {
    this.resetSelection();
  }

  protected async upload(): Promise<void> {
    const image = this.selectedImage();
    if (!image) return;

    this.errorMessage.set(null);
    this.loading.set(true);
    this.result.set(null);

    try {
      const pngBlob = await this.ensurePng(image);

      const form = new FormData();
      form.append('file', pngBlob, 'upload.png');

      const resp = await fetch('http://127.0.0.1:8001/upload', {
        method: 'POST',
        body: form,
      });

      if (!resp.ok) {
        const text = await resp.text();
        throw new Error(text || resp.statusText);
      }

      const data = await resp.json();
      this.result.set(data);
    } catch (err: any) {
      this.errorMessage.set(String(err?.message ?? err));
    } finally {
      this.loading.set(false);
    }
  }

  ngOnDestroy(): void {
    this.revokePreviewUrl();
  }

  private applyImage(image: File | null): void {
    this.revokePreviewUrl();
    this.selectedImage.set(image);

    if (!image) {
      this.previewUrl.set(null);
      return;
    }

    const objectUrl = URL.createObjectURL(image);
    this.previewUrl.set(objectUrl);
  }

  private resetSelection(): void {
    this.errorMessage.set(null);
    this.applyImage(null);
  }

  private revokePreviewUrl(): void {
    const currentUrl = this.previewUrl();

    if (currentUrl) {
      URL.revokeObjectURL(currentUrl);
    }
  }

  private formatFileSize(bytes: number): string {
    if (bytes < 1024) {
      return `${bytes} B`;
    }

    const units = ['KB', 'MB', 'GB'];
    let size = bytes / 1024;
    let unitIndex = 0;

    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex += 1;
    }

    return `${size.toFixed(size >= 10 ? 0 : 1)} ${units[unitIndex]}`;
  }

  private ensurePng(file: File): Promise<Blob> {
    if (file.type === 'image/png') {
      return Promise.resolve(file);
    }

    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement('canvas');
        canvas.width = img.width;
        canvas.height = img.height;
        const ctx = canvas.getContext('2d');
        if (!ctx) return reject(new Error('Canvas not supported'));
        ctx.drawImage(img, 0, 0);
        canvas.toBlob((blob) => {
          if (!blob) return reject(new Error('Failed to convert image'));
          resolve(blob);
        }, 'image/png');
      };
      img.onerror = (e) => reject(new Error('Failed to load image for conversion'));
      img.src = URL.createObjectURL(file);
    });
  }
}
