/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  allowedDevOrigins: [
    '192.168.8.103',
    // Alternatively, you can use a wildcard or your local host IP
  ],
}

export default nextConfig
