#include <stdint.h>

#define FFT_BASE       0x03000000
#define FFT_CTRL       (*(volatile uint32_t*)(FFT_BASE + 0x00))
#define FFT_STATUS     (*(volatile uint32_t*)(FFT_BASE + 0x04))
#define FFT_IN_WORD(i) (*(volatile uint32_t*)(FFT_BASE + 0x08  + 4*(i)))
#define FFT_OUT_WORD(i)(*(volatile uint32_t*)(FFT_BASE + 0x108 + 4*(i)))

static void delay(int n) {
    for (volatile int i = 0; i < n * 1000; i++);
}

int main(void) {
    uint16_t input_re[64];
    uint16_t input_im[64];
    uint16_t output_re[64];
    uint16_t output_im[64];

    // 1. Initialize test pattern (ramp input)
    for (int i = 0; i < 64; i++) {
        input_re[i] = 1;  // 0,1,2,...
        input_im[i] = 0;
    }

    // 2. Load 64 complex samples into FFT accelerator buffer
    for (int i = 0; i < 64; i++) {
        uint32_t packed = ((uint32_t)input_im[i] << 16) | (input_re[i] & 0xFFFF);
        FFT_IN_WORD(i) = packed;
    }

    // 3. Start FFT
    FFT_CTRL = 0x1;

    // 4. Wait for completion
    while ((FFT_STATUS & 0x1) == 0) {
        // optional delay to avoid tight polling
        delay(1);
    }

    // 5. Read results
    for (int i = 0; i < 64; i++) {
        uint32_t packed = FFT_OUT_WORD(i);
        output_re[i] = (uint16_t)(packed & 0xFFFF);
        output_im[i] = (uint16_t)((packed >> 16) & 0xFFFF);
    }

    // 6. Clear DONE/IRQ flag
    FFT_CTRL = 0x2;

#ifdef UART_BASE
    for (int i = 0; i < 64; i++) {
        printf("FFT[%02d] = %d + j%d\n", i,
               (int16_t)output_re[i],
               (int16_t)output_im[i]);
    }
#endif

    while (1);
    return 0;
}
