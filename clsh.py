import os
import math

from PIL import Image


# Helper function to convert large chunks of data to RGBA-like hex codes
def bytes_to_large_hex(chunk):
    # Fill with zeros if chunk is smaller than the expected size
    if len(chunk) < 8:
        chunk = chunk.ljust(8, b"\x00")

    # Convert 8 bytes into a single large integer and return it as a hex string
    large_value = int.from_bytes(chunk, byteorder="big")
    return f"{large_value:08x}"


# Helper function to convert large hex code into RGBA values
def large_hex_to_rgba(hex_value):
    large_value = int(hex_value, 16)

    # Extract R, G, B, and A components
    r = (large_value >> 24) & 0xFF
    g = (large_value >> 16) & 0xFF
    b = (large_value >> 8) & 0xFF
    a = large_value & 0xFF

    return (r, g, b, a)


# Helper function to convert RGBA values back to bytes
def rgba_to_bytes(rgba):
    large_value = (rgba[0] << 24) + (rgba[1] << 16) + (rgba[2] << 8) + rgba[3]
    return large_value.to_bytes(8, byteorder="big")


# Mode 1: Convert file to CLSH format and generate PNG
def convert_to_clsh(input_file, output_clsh, output_png):
    file_size = os.path.getsize(input_file)
    num_chunks = math.ceil(file_size / 8)  # Each chunk is 8 bytes

    # Calculate the size of the PNG (try to make it square-like)
    img_size = math.ceil(math.sqrt(num_chunks))

    with open(input_file, "rb") as f_in, open(output_clsh, "w") as f_out:
        # Create an empty image with RGBA mode
        img = Image.new("RGBA", (img_size, img_size), (0, 0, 0, 0))
        pixels = img.load()

        # Process the input file chunk by chunk (8 bytes per chunk)
        pixel_idx = 0
        while True:
            chunk = f_in.read(8)
            if not chunk:
                break

            # Convert the chunk to a large hex code
            hex_code = bytes_to_large_hex(chunk)
            f_out.write(f"{hex_code} ")  # Write to CLSH file

            # Convert the hex code to RGBA values
            rgba = large_hex_to_rgba(hex_code)

            # Map the RGBA to the image pixel
            x, y = divmod(pixel_idx, img_size)
            pixels[x, y] = rgba
            pixel_idx += 1

        # Fill remaining pixels with filler (0, 0, 0, 0) if needed
        for i in range(pixel_idx, img_size * img_size):
            x, y = divmod(i, img_size)
            pixels[x, y] = (0, 0, 0, 0)

        # Save the image
        img.save(output_png)

    print(f"Conversion completed: {output_clsh}, {output_png}")


# Mode 2: Revert CLSH format to original file
def revert_from_clsh(input_clsh, output_file):
    with open(input_clsh, "r") as f_clsh, open(output_file, "wb") as f_out:
        hex_values = f_clsh.read().split()

        # Process the hex values in the CLSH file
        for hex_code in hex_values:
            byte_chunk = rgba_to_bytes(large_hex_to_rgba(hex_code))
            f_out.write(byte_chunk)

        print(f"Reversion to original file completed: {output_file}")


# Main program
def main():
    mode = input("Enter mode (1: Convert, 2: Revert): ").strip()
    file_path = input("Enter file path: ").strip()

    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist.")
        return

    if mode == "1":
        # Convert mode
        clsh_path = input("Enter output .clsh file path: ").strip()
        png_path = input("Enter output .png file path: ").strip()
        convert_to_clsh(file_path, clsh_path, png_path)
    elif mode == "2":
        # Revert mode
        clsh_path = file_path  # Assuming the input is the .clsh file path
        output_file_path = input("Enter output file path: ").strip()
        revert_from_clsh(clsh_path, output_file_path)
    else:
        print("Error: Invalid mode selected.")


if __name__ == "__main__":
    main()
