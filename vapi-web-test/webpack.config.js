const path = require("path");
const HtmlWebpackPlugin = require("html-webpack-plugin");

module.exports = {
  resolve: {
    modules: [
      path.resolve(__dirname, 'node_modules'),
      path.resolve(__dirname, 'custom_modules'), // Add custom module paths here
    ],
  },
  entry: "./app.js",
  output: {
    filename: "bundle.js",
    path: path.resolve(__dirname, "dist"),
    // publicPath: '/',
  },
  mode: "development",
  devServer: {
   
    allowedHosts: 'all',
    static: {
      directory: path.join(__dirname, "/"), // Serve from the root
    },
    compress: true,
    port: 9000,
    hot: true,
    open: true,
  },
  plugins: [
    new HtmlWebpackPlugin({
      template: "./index.html",
      filename: "index.html",
    }),
    new HtmlWebpackPlugin({
      template: "./call.html",
      filename: "call.html",
    }),
  ],
  module: {
    rules: [
      {
        test: /\.(mp3)$/,
        include: path.resolve(__dirname, "resource"),
        use: [
          {
            loader: "file-loader",
            options: {
              name: "[name].[ext]",
              outputPath: "resource/", // Output path within 'dist' folder
            },
          },
        ],
      },
      {
        test: /\.css$/,
        include: path.resolve(__dirname, "style"),
        use: ["style-loader", "css-loader"],
      },
    ],
  },
};



