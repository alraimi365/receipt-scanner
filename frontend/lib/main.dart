import 'package:flutter/material.dart';
import 'dart:io';
import 'package:image_picker/image_picker.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:flutter_dotenv/flutter_dotenv.dart';

void main() async {
  // Load environment variables
  await dotenv.load(fileName: ".env");

  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Receipt Scanner',
      theme: ThemeData(
        primarySwatch: Colors.blue,
      ),
      home: const MyHomePage(title: 'Receipt Scanner'),
    );
  }
}

class MyHomePage extends StatefulWidget {
  const MyHomePage({super.key, required this.title});

  final String title;

  @override
  State<MyHomePage> createState() => _MyHomePageState();
}

class _MyHomePageState extends State<MyHomePage> {
  File? _image;
  final ImagePicker _picker = ImagePicker();
  dynamic _apiResponse; // Allow for dynamic structures
  bool _isLoading = false;
  String _errorMessage = "";

  // Function to pick an image
  Future<void> _pickImage(ImageSource source) async {
    final pickedFile = await _picker.pickImage(source: source);

    if (pickedFile != null) {
      setState(() {
        _image = File(pickedFile.path);
        _errorMessage = "";
      });

      await _sendImageToApi(File(pickedFile.path));
    } else {
      _showSnackBar("No image selected!");
    }
  }

  // Function to send the image to the API
  Future<void> _sendImageToApi(File image) async {
    String backendUrl = dotenv.env['BACKEND_URL'] ?? 'http://127.0.0.1:5001';
    final url = Uri.parse('$backendUrl/upload_receipt');

    setState(() {
      _isLoading = true;
      _apiResponse = null;
    });

    try {
      final request = http.MultipartRequest("POST", url);
      request.files
          .add(await http.MultipartFile.fromPath('receipt', image.path));

      final response = await request.send();
      final responseBody = await response.stream.bytesToString();

      if (response.statusCode == 200) {
        final parsedResponse = json.decode(responseBody);
        setState(() {
          _apiResponse = parsedResponse;
        });
        _showSnackBar("Receipt processed successfully!");
      } else {
        setState(() {
          _errorMessage = "Error: ${response.statusCode}";
        });
        _showSnackBar("Failed to process the receipt.");
      }
    } catch (e) {
      setState(() {
        _errorMessage = "Failed to connect to the server.";
      });
      _showSnackBar("Connection error. Please try again.");
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  // Function to show a snackbar
  void _showSnackBar(String message) {
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text(message)));
  }

  // Recursive widget to handle nested JSON
  Widget _buildJsonTree(dynamic data) {
    if (data is Map) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: data.entries.map((entry) {
          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                "${entry.key}:",
                style: const TextStyle(fontWeight: FontWeight.bold),
              ),
              _buildJsonTree(entry.value),
            ],
          );
        }).toList(),
      );
    } else if (data is List) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: data.map((item) => _buildJsonTree(item)).toList(),
      );
    } else {
      return Text(data.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.title),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                ElevatedButton.icon(
                  onPressed: () {
                    showModalBottomSheet(
                      context: context,
                      builder: (context) => Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          ListTile(
                            leading: const Icon(Icons.photo_library),
                            title: const Text("Choose from Gallery"),
                            onTap: () {
                              Navigator.pop(context);
                              _pickImage(ImageSource.gallery);
                            },
                          ),
                          ListTile(
                            leading: const Icon(Icons.camera_alt),
                            title: const Text("Take a Picture"),
                            onTap: () {
                              Navigator.pop(context);
                              _pickImage(ImageSource.camera);
                            },
                          ),
                        ],
                      ),
                    );
                  },
                  icon: const Icon(Icons.upload_file),
                  label: const Text("Upload Receipt"),
                ),
              ],
            ),
            const SizedBox(height: 20),
            if (_isLoading)
              const CircularProgressIndicator()
            else if (_image != null)
              Column(
                children: [
                  Image.file(_image!, height: 200, fit: BoxFit.cover),
                  const SizedBox(height: 10),
                  Text("File: ${_image!.path.split('/').last}"),
                ],
              ),
            const SizedBox(height: 20),
            if (_errorMessage.isNotEmpty)
              Text(
                _errorMessage,
                style: const TextStyle(color: Colors.red),
              ),
            const SizedBox(height: 10),
            if (_apiResponse != null)
              Expanded(
                child: SingleChildScrollView(
                  child: Container(
                    padding: const EdgeInsets.all(16.0),
                    decoration: BoxDecoration(
                      color: Colors.grey[200],
                      borderRadius: BorderRadius.circular(8.0),
                    ),
                    child: _buildJsonTree(
                        _apiResponse), // Recursive JSON rendering
                  ),
                ),
              ),
            if (_apiResponse == null && !_isLoading)
              const Text(
                "No response yet. Upload a receipt to get started.",
                style: TextStyle(color: Colors.black54),
              ),
          ],
        ),
      ),
    );
  }
}
