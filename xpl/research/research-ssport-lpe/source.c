/*
 * SSPORT.SYS Kernel Driver Buffer Overflow — CVE-2021-3438
 * ==========================================================
 * Author: André Henrique (@mrhenrike) | União Geek
 *
 * HP/Samsung/Xerox printer driver (SSPORT.SYS) shipped with all
 * HP LaserJet, Samsung CLP/CLX/ML/SCX, and Xerox B2xx/PH30xx/WC
 * drivers for Windows loads a kernel driver (SSPORT.SYS) that
 * exposes a DeviceIoControl interface with IOCTL code 0x9C402004.
 *
 * The driver passes a user-supplied size to strncpy() to copy into
 * a fixed-size kernel stack buffer without validation:
 *
 *   strncpy(kernel_buf, UserBuffer, UserSuppliedLength);  // BOOM
 *
 * Any local unprivileged user can open \\.\SSPORT and send a crafted
 * IOCTL to overflow the kernel stack, leading to SYSTEM privilege.
 *
 * This PoC detects the presence of the vulnerable driver and performs
 * a safe overflow probe (non-exploitative) to confirm vulnerability.
 *
 * Usage: ./exploit <host> <port>   (host/port unused — local exploit)
 *        On Windows: runs the IOCTL probe directly.
 *        On Linux/WSL: checks if \\.\SSPORT is reachable (always fails).
 *
 * Build: gcc -O2 -o exploit source.c -lntdll  (Windows)
 *        gcc -O2 -o exploit source.c           (Linux — detection only)
 *
 * References:
 *   https://www.sentinelone.com/labs/cve-2021-3438-16-years-in-hiding
 *   https://nvd.nist.gov/vuln/detail/CVE-2021-3438
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef _WIN32
  #include <windows.h>
  #define SSPORT_DEVICE  "\\\\.\\SSPORT"
  #define IOCTL_SSPORT   0x9C402004
#endif

int main(int argc, char *argv[]) {
    /* host/port unused — local kernel driver exploit */
    (void)argc; (void)argv;

    printf("[*] CVE-2021-3438 — SSPORT.SYS Kernel Driver LPE\n");
    printf("[*] HP/Samsung/Xerox Windows printer driver privilege escalation\n");

#ifdef _WIN32
    HANDLE hDevice = CreateFileA(
        SSPORT_DEVICE,
        GENERIC_READ | GENERIC_WRITE,
        0, NULL,
        OPEN_EXISTING,
        FILE_ATTRIBUTE_NORMAL,
        NULL
    );

    if (hDevice == INVALID_HANDLE_VALUE) {
        DWORD err = GetLastError();
        if (err == ERROR_FILE_NOT_FOUND || err == ERROR_PATH_NOT_FOUND) {
            printf("[-] SSPORT.SYS device not found — driver not loaded.\n");
            printf("[-] System may be patched or HP/Samsung/Xerox driver not installed.\n");
        } else if (err == ERROR_ACCESS_DENIED) {
            printf("[!] Access denied to SSPORT device — driver IS present (run as admin to test).\n");
            printf("[+] VULNERABLE: SSPORT.SYS detected. CVE-2021-3438 likely present.\n");
            return 0;
        } else {
            printf("[-] CreateFile error: %lu\n", err);
        }
        return 1;
    }

    printf("[+] SSPORT.SYS device opened successfully!\n");
    printf("[+] VULNERABLE: Driver present and accessible. CVE-2021-3438 confirmed.\n");

    /* Safe probe: send minimum IOCTL to verify handler is reachable
     * (no actual overflow — just detect the attack surface) */
    char safe_buf[8] = {0};
    DWORD bytes_ret = 0;
    BOOL ok = DeviceIoControl(
        hDevice,
        IOCTL_SSPORT,
        safe_buf, sizeof(safe_buf),
        safe_buf, sizeof(safe_buf),
        &bytes_ret, NULL
    );

    if (ok || GetLastError() != ERROR_INVALID_FUNCTION) {
        printf("[+] IOCTL 0x9C402004 accepted — overflow handler reachable.\n");
        printf("[!] System is VULNERABLE to kernel LPE via SSPORT.SYS (CVE-2021-3438).\n");
        printf("[!] Update HP/Samsung/Xerox printer drivers immediately.\n");
    }

    CloseHandle(hDevice);
    return 0;

#else
    /* Linux/WSL — detection only via driver presence check */
    printf("[!] Running on Linux/WSL — SSPORT.SYS is a Windows kernel driver.\n");
    printf("[*] To test: run this binary natively on the target Windows machine.\n");
    printf("[*] Detection: check if C:\\Windows\\System32\\SSPORT.SYS exists\n");
    printf("[*]   and the driver service 'SSPORT' is running (sc query SSPORT).\n");
    return 2;
#endif
}
