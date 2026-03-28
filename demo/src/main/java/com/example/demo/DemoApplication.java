package com.example.demo;

import io.github.cdimascio.dotenv.Dotenv;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class DemoApplication {

	public static void main(String[] args) {
		loadDotenvDirectory("..");
		loadDotenvDirectory("src/main/resources");

		SpringApplication.run(DemoApplication.class, args);
	}

	private static void loadDotenvDirectory(String directory) {
		Dotenv dotenv = Dotenv.configure()
				.directory(directory)
				.ignoreIfMissing()
				.load();

		dotenv.entries().forEach(entry -> {
			if (System.getProperty(entry.getKey()) == null) {
				System.setProperty(entry.getKey(), entry.getValue());
			}
		});
	}

}
