import { Component, OnDestroy, computed, signal } from '@angular/core';

@Component({
  selector: 'app-root',
  imports: [],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App implements OnDestroy {
  protected readonly title = 'Image intake landing page';
  protected readonly selectedImage = signal<File | null>(null);
  protected readonly previewUrl = signal<string | null>(null);
  protected readonly errorMessage = signal<string | null>(null);

  protected readonly fileName = computed(() => this.selectedImage()?.name ?? 'No image selected yet');
  protected readonly fileMeta = computed(() => {
    const image = this.selectedImage();

    if (!image) {
      return 'PNG, JPG, GIF, WEBP';
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
}
